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

  if (!audio) {
    return;
  }

  var trekAktif = null;

  function pesan(kunci) {
    var kotak = document.getElementById('collection-messages');
    return kotak ? (kotak.getAttribute('data-msg-' + kunci) || '') : '';
  }

  function tampilkanGalat(teks) {
    var pesanGalat = teks || 'Audio tidak dapat diputar.';
    if (window.KX && typeof window.KX.toast === 'function') {
      window.KX.toast(pesanGalat, 'danger');
    } else {
      var kotak = document.getElementById('collection-alert');
      if (kotak) {
        kotak.textContent = pesanGalat;
        kotak.hidden = false;
      }
    }
  }

  function tampilkanSukses(teks) {
    if (window.KX && typeof window.KX.toast === 'function') {
      window.KX.toast(teks, 'success');
    }
  }

  function mintaGrant(scope, resource) {
    return new Promise(function (selesai) {
      var penangan = function (event) {
        var detail = event.detail || {};
        if (detail.scope !== scope || String(detail.resource || '') !== String(resource || '')) {
          return;
        }
        document.removeEventListener('cryptix:reauth-grant', penangan);
        selesai(detail.token);
      };
      document.addEventListener('cryptix:reauth-grant', penangan);

      var pemicu = document.createElement('button');
      pemicu.type = 'button';
      pemicu.hidden = true;
      pemicu.setAttribute('data-reauth', scope);
      pemicu.setAttribute('data-reauth-resource', String(resource || ''));
      document.body.appendChild(pemicu);
      pemicu.click();
      document.body.removeChild(pemicu);
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

  var cadanganMime = {
    mp3: 'audio/mpeg',
    wav: 'audio/wav',
    flac: 'audio/flac',
    ogg: 'audio/ogg',
    m4a: 'audio/mp4'
  };

  if (audio) {
    audio.addEventListener('error', function () {
      tampilkanGalat('Audio tidak dapat diputar.');
    });
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
        throw new Error('Audio tidak dapat diputar.');
      }
      var headerType = resp.headers.get('Content-Type') || '';
      var bagianType = headerType.split(';')[0].trim();
      var ekstensi = (nama.split('.').pop() || '').toLowerCase();
      var tipeBlob = bagianType || cadanganMime[ekstensi] || 'audio/mpeg';

      return resp.arrayBuffer().then(function (buf) {
        return new Blob([buf], { type: tipeBlob });
      });
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
        janji.catch(function () {
          tampilkanGalat('Audio tidak dapat diputar.');
        });
      }
    }).catch(function (err) {
      tampilkanGalat('Audio tidak dapat diputar.');
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
