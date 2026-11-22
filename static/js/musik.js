/**
 * static/js/musik.js
 * ─────────────────
 * Pemutar audio modal halaman Audio (U2g):
 * - Memutar audio HTML5 untuk trek terenkripsi (stream/view URL) di modal KX.modal.
 * - Tombol play bulat di setiap baris membuka modal dengan <audio controls> native.
 * - Menutup modal menghentikan audio dan melepas sumbernya.
 * - Pencarian trek lokal di sisi klien (memfilter baris tabel).
 * - Checkbox pilih semua dan sinkronisasi dengan KX.aksiMengambang.
 * - Menu ⋯ per baris: Kunci/Lepas kunci, Buka di Winamp, Unduh, Hapus (ke Sampah dengan grant item.delete).
 * - Integrasi dengan CryptixLock untuk trek terkunci.
 */
(function () {
  'use strict';

  var audio = document.getElementById('music-audio');
  var modalAudio = document.getElementById('audio-modal');
  var judulModal = document.getElementById('audio-modal-title');
  var kotakCari = document.getElementById('audio-search');
  var pilihSemua = document.getElementById('audio-select-all');
  var bilahPilih = document.getElementById('selection-bar');
  var jumlahPilih = document.getElementById('selection-count');
  var tombolKunciMassal = document.getElementById('lock-items-button');
  var tombolLepasMassal = document.getElementById('unlock-items-button');

  if (!audio) {
    return;
  }

  var trekAktif = null;

  function pesan(kunci) {
    var kotak = document.getElementById('collection-messages');
    return kotak ? (kotak.getAttribute('data-msg-' + kunci) || '') : '';
  }

  function tampilkanGalat(teks) {
    var kotak = document.getElementById('collection-alert');
    if (kotak) {
      kotak.textContent = teks || pesan('error');
      kotak.hidden = false;
    } else if (window.KX && window.KX.toast) {
      window.KX.toast(teks || pesan('error'), 'danger');
    }
  }

  function tampilkanSukses(teks) {
    if (window.KX && typeof window.KX.toast === 'function') {
      window.KX.toast(teks, 'success');
    }
  }

  function urai(resp) {
    return resp.json().catch(function () { return {}; }).then(function (data) {
      if (!resp.ok || data.success === false) {
        throw new Error(data.error || pesan('error'));
      }
      return data;
    });
  }

  function kirim(url, data, grant) {
    var headers = { 'Content-Type': 'application/json' };
    if (grant) headers['X-Reauth-Grant'] = grant;
    return apiFetch(url, {
      method: 'POST',
      headers: headers,
      body: JSON.stringify(data || {}),
      credentials: 'same-origin'
    }).then(urai);
  }

  function grantUntuk(scope, resource) {
    if (!window.CryptixReauth || typeof window.CryptixReauth.grantFor !== 'function') {
      return null;
    }
    return window.CryptixReauth.grantFor(scope, resource);
  }

  function mintaGrant(scope, resource) {
    if (window.CryptixLock && typeof window.CryptixLock.mintaGrant === 'function') {
      return window.CryptixLock.mintaGrant(scope, resource);
    }
    var token = grantUntuk(scope, resource);
    if (token) {
      return Promise.resolve(token);
    }
    return Promise.reject(new Error(pesan('error')));
  }

  function ubahStatus(kartu, state, grant) {
    var id = kartu.getAttribute('data-file-id');
    var koleksi = kartu.getAttribute('data-collection-id');
    if (koleksi) {
      return kirim('/api/collections/' + koleksi + '/items/state', {
        file_ids: [Number(id)],
        state: state
      }, state === 'normal' ? grant : null);
    }
    return kirim('/api/media/' + id + '/state', {
      state: state
    }, state === 'normal' ? grant : null);
  }

  function ikonKartu(nama) {
    return '<svg class="kx-icon" width="16" height="16" aria-hidden="true" ' +
      'focusable="false"><use href="/static/icons/sprite.svg#' + nama +
      '"></use></svg>';
  }

  function perbaruiStatusKartu(kartu, state) {
    var terkunci = state === 'locked';
    kartu.setAttribute('data-locked', terkunci ? '1' : '0');
    kartu.classList.toggle('item-terkunci', terkunci);
    var putar = kartu.querySelector('[data-track-play]');
    if (putar) {
      putar.innerHTML = ikonKartu(terkunci ? 'lock' : 'play');
    }
    var lencana = kartu.querySelector('.kx-badge');
    if (lencana) {
      lencana.textContent = terkunci ? 'Terkunci' : 'Terenkripsi';
      lencana.className = terkunci
        ? 'kx-badge kx-badge-warn item-lock-note'
        : 'kx-badge kx-badge-ok';
    }
    var aksi = kartu.querySelector('[data-track-lock], [data-track-unlock]');
    if (aksi) {
      var label = aksi.querySelector('span');
      if (terkunci) {
        aksi.removeAttribute('data-track-lock');
        aksi.setAttribute('data-track-unlock', '');
        if (label) label.textContent = 'Lepas kunci';
      } else {
        aksi.removeAttribute('data-track-unlock');
        aksi.setAttribute('data-track-lock', '');
        if (label) label.textContent = 'Kunci';
      }
    }
  }

  function kunciKartu(kartu) {
    ubahStatus(kartu, 'locked').then(function () {
      perbaruiStatusKartu(kartu, 'locked');
      tampilkanSukses('Trek berhasil dikunci.');
    }).catch(function (err) {
      tampilkanGalat(err.message);
    });
  }

  function lepasKunciKartu(kartu) {
    var resource = kartu.getAttribute('data-collection-id') ||
      kartu.getAttribute('data-file-id');
    mintaGrant('item.unlock', resource).then(function (token) {
      return ubahStatus(kartu, 'normal', token);
    }).then(function () {
      perbaruiStatusKartu(kartu, 'normal');
      tampilkanSukses('Kunci trek berhasil dilepas.');
    }).catch(function (err) {
      tampilkanGalat(err.message);
    });
  }

  function kartuTerpilih() {
    var hasil = [];
    document.querySelectorAll('[data-select-file]:checked').forEach(function (cb) {
      var kartu = cb.closest('[data-track]');
      if (kartu) hasil.push(kartu);
    });
    return hasil;
  }

  function aksiMassal(state) {
    var kartuList = kartuTerpilih();
    if (!kartuList.length) return;
    var rantai = Promise.resolve();
    kartuList.forEach(function (kartu) {
      rantai = rantai.then(function () {
        if (state === 'normal') {
          var resource = kartu.getAttribute('data-collection-id') ||
            kartu.getAttribute('data-file-id');
          return mintaGrant('item.unlock', resource).then(function (token) {
            return ubahStatus(kartu, 'normal', token);
          }).then(function () {
            perbaruiStatusKartu(kartu, 'normal');
          });
        }
        return ubahStatus(kartu, 'locked').then(function () {
          perbaruiStatusKartu(kartu, 'locked');
        });
      });
    });
    rantai.then(function () {
      tampilkanSukses(state === 'normal'
        ? 'Kunci trek berhasil dilepas.'
        : 'Trek berhasil dikunci.');
      document.querySelectorAll('[data-select-file]:checked').forEach(function (cb) {
        cb.checked = false;
      });
      perbaruiPilihan();
    }).catch(function (err) {
      tampilkanGalat(err.message);
    });
  }

  function perbaruiPilihan() {
    var jumlah = document.querySelectorAll('[data-select-file]:checked').length;
    if (bilahPilih) bilahPilih.hidden = jumlah === 0;
    if (jumlahPilih) jumlahPilih.textContent = jumlah + ' dipilih';
    if (window.KX && window.KX.aksiMengambang) {
      window.KX.aksiMengambang.segarkan();
    }
  }

  function bolehDiputar(kartu) {
    if (!kartu) {
      return false;
    }
    if (kartu.getAttribute('data-locked') !== '1') {
      return true;
    }
    return Boolean(window.CryptixReauth &&
      window.CryptixReauth.grantFor('item.view', kartu.getAttribute('data-file-id')));
  }

  var blobAktif = null;

  function hentikanAudio() {
    if (audio) {
      audio.pause();
      audio.removeAttribute('src');
      audio.load();
    }
    if (blobAktif) {
      URL.revokeObjectURL(blobAktif);
      blobAktif = null;
    }
    if (trekAktif) {
      trekAktif.classList.remove('is-playing');
      trekAktif = null;
    }
    if (modalAudio) {
      modalAudio.classList.remove('is-open');
      modalAudio.setAttribute('aria-hidden', 'true');
      modalAudio.hidden = true;
    }
  }

  function putarKartu(kartu) {
    if (!kartu) {
      return;
    }
    var fileId = kartu.getAttribute('data-file-id');
    var streamUrl = kartu.getAttribute('data-stream-url') || ('/media-vault/stream/' + fileId);
    var nama = kartu.getAttribute('data-name') || 'Audio';

    mintaGrant('audio.play', fileId).then(function (token) {
      return apiFetch(streamUrl, {
        method: 'GET',
        headers: {
          'X-Reauth-Grant': token
        },
        credentials: 'same-origin'
      });
    }).then(function (resp) {
      if (!resp.ok) {
        throw new Error(pesan('error') || 'Gagal memutar audio.');
      }
      return resp.blob();
    }).then(function (blob) {
      hentikanAudio();

      if (trekAktif && trekAktif !== kartu) {
        trekAktif.classList.remove('is-playing');
      }
      trekAktif = kartu;
      kartu.classList.add('is-playing');

      if (judulModal) {
        judulModal.textContent = nama;
      }

      blobAktif = URL.createObjectURL(blob);
      audio.src = blobAktif;
      audio.load();

      if (modalAudio) {
        modalAudio.hidden = false;
        if (window.KX && window.KX.modal && typeof window.KX.modal.buka === 'function') {
          window.KX.modal.buka(modalAudio);
        } else {
          modalAudio.classList.add('is-open');
          modalAudio.setAttribute('aria-hidden', 'false');
        }
      }

      var janji = audio.play();
      if (janji && typeof janji.catch === 'function') {
        janji.catch(function () {});
      }
    }).catch(function (err) {
      tampilkanGalat(err && err.message ? err.message : pesan('error'));
    });
  }

  // Klik putar pada tabel
  document.addEventListener('click', function (event) {
    var pemicu = event.target.closest('[data-track-play], .music-track-name, .kx-audio-track-title');
    if (!pemicu) {
      return;
    }
    var kartu = pemicu.closest('[data-track]');
    if (!kartu) {
      return;
    }
    if (!bolehDiputar(kartu)) {
      if (window.CryptixLock) {
        window.CryptixLock.pilih(kartu, putarKartu, 'item.view');
      }
      return;
    }
    putarKartu(kartu);
  });

  // Tutup modal audio
  if (modalAudio) {
    modalAudio.addEventListener('click', function (e) {
      if (e.target.closest('[data-kx-tutup]') || e.target === modalAudio) {
        hentikanAudio();
      }
    });

    if (window.MutationObserver) {
      var obs = new MutationObserver(function () {
        if (!modalAudio.classList.contains('is-open') || modalAudio.getAttribute('aria-hidden') === 'true') {
          if (audio.src || blobAktif) {
            hentikanAudio();
          }
        }
      });
      obs.observe(modalAudio, { attributes: true, attributeFilter: ['class', 'aria-hidden'] });
    }
  }

  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && modalAudio && modalAudio.classList.contains('is-open')) {
      hentikanAudio();
    }
  });

  // Aksi Kunci / Lepas kunci per item dan massal
  document.addEventListener('click', function (event) {
    var kunci = event.target.closest('[data-track-lock]');
    if (kunci) {
      var kartuKunci = kunci.closest('[data-track]');
      if (kartuKunci) kunciKartu(kartuKunci);
      return;
    }
    var lepas = event.target.closest('[data-track-unlock]');
    if (lepas) {
      var kartuLepas = lepas.closest('[data-track]');
      if (kartuLepas) lepasKunciKartu(kartuLepas);
      return;
    }
    if (event.target === tombolKunciMassal) {
      aksiMassal('locked');
      return;
    }
    if (event.target === tombolLepasMassal) {
      aksiMassal('normal');
      return;
    }
  });

  document.addEventListener('change', function (event) {
    if (event.target.matches('[data-select-file]')) {
      perbaruiPilihan();
    }
  });

  // ── Pencarian trek di sisi klien ─────────────────────────────────────────
  if (kotakCari) {
    kotakCari.addEventListener('input', function () {
      var kueri = kotakCari.value.trim().toLowerCase();
      var barisList = document.querySelectorAll('[data-track]');
      barisList.forEach(function (tr) {
        var nama = (tr.getAttribute('data-name') || '').toLowerCase();
        var cocok = !kueri || nama.indexOf(kueri) !== -1;
        tr.hidden = !cocok;
      });
      var pesanTakAda = document.getElementById('audio-no-results');
      var tabelWrap = document.querySelector('.kx-card-body > .kx-table-wrap');
      if (pesanTakAda) {
        var adaYangTampil = Array.prototype.some.call(barisList, function (tr) { return !tr.hidden; });
        pesanTakAda.hidden = barisList.length === 0 || adaYangTampil;
        if (tabelWrap && barisList.length > 0) {
          tabelWrap.hidden = !adaYangTampil;
        }
      }
    });
  }

  // ── Checkbox pilih semua & sinkronisasi ──────────────────────────────────
  if (pilihSemua) {
    pilihSemua.addEventListener('change', function () {
      var cek = pilihSemua.checked;
      document.querySelectorAll('[data-select-file]').forEach(function (cb) {
        var tr = cb.closest('[data-track]');
        if (tr && !tr.hidden) {
          cb.checked = cek;
          cb.dispatchEvent(new Event('change', { bubbles: true }));
        }
      });
    });
  }

  // ── Menu titik tiga (⋯) ──────────────────────────────────────────────────
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') {
      document.querySelectorAll('[data-menu-dropdown]').forEach(function (d) {
        d.hidden = true;
      });
    }
  });

  document.addEventListener('click', function (event) {
    var tombolMenu = event.target.closest('[data-menu-toggle]');
    var semuaMenu = document.querySelectorAll('[data-menu-dropdown]');

    if (tombolMenu) {
      event.stopPropagation();
      var wrap = tombolMenu.closest('.kx-audio-menu-wrap');
      var dropdown = wrap ? wrap.querySelector('[data-menu-dropdown]') : null;
      var isOpen = dropdown && !dropdown.hidden;
      semuaMenu.forEach(function (d) { d.hidden = true; });
      if (dropdown) {
        dropdown.hidden = isOpen;
        if (!isOpen) {
          dropdown.classList.remove('kx-audio-menu-atas');
          var rect = dropdown.getBoundingClientRect();
          var batasBawah = (window.innerHeight || document.documentElement.clientHeight) - 16;
          if (rect.bottom > batasBawah) {
            dropdown.classList.add('kx-audio-menu-atas');
          }
        }
      }
      return;
    }

    semuaMenu.forEach(function (d) { d.hidden = true; });
  });

  // Sinkronisasi checkbox data-kx-pilih
  function sinkronPilihan() {
    document.querySelectorAll('[data-select-file]').forEach(function (cb) {
      if (!cb.hasAttribute('data-kx-pilih')) {
        cb.setAttribute('data-kx-pilih', '');
      }
    });
    if (window.KX && window.KX.aksiMengambang) {
      window.KX.aksiMengambang.segarkan();
    }
  }

  document.addEventListener('collection:items-loaded', sinkronPilihan);
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', sinkronPilihan);
  } else {
    sinkronPilihan();
  }

  perbaruiPilihan();
})();
