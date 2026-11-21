/**
 * static/js/musik.js
 * ─────────────────
 * Pemutar audio kustom halaman Audio (U2b P5):
 * - Memutar audio HTML5 untuk trek terenkripsi (stream/view URL)
 * - Pemutar kustom di bagian bawah layar: cover placeholder, judul, format,
 *   prev/next, play toggle (lingkaran teal), waktu berjalan, progress bar teal, total durasi.
 * - Tombol play bulat di setiap baris tabel.
 * - Pencarian trek lokal di sisi klien (memfilter baris tabel).
 * - Checkbox pilih semua dan sinkronisasi dengan KX.aksiMengambang.
 * - Menu ⋯ per baris: Kunci/Lepas kunci, Buka di Winamp, Unduh, Hapus (ke Sampah via KX.konfirmasiHapus).
 * - Integrasi dengan CryptixLock untuk trek terkunci.
 */
(function () {
  'use strict';

  var audio = document.getElementById('music-audio');
  var judulBawah = document.getElementById('music-now-playing');
  var subBawah = document.getElementById('music-now-sub');
  var tombolPutar = document.getElementById('music-play-toggle');
  var tombolSebelum = document.getElementById('music-prev');
  var tombolSesudah = document.getElementById('music-next');
  var formWinamp = document.getElementById('music-winamp-form');
  var tombolWinamp = document.getElementById('music-winamp');
  var waktuKini = document.getElementById('music-time-cur');
  var waktuTotal = document.getElementById('music-time-total');
  var barKemajuan = document.getElementById('music-progress-bar');
  var isiKemajuan = document.getElementById('music-progress-fill');
  var kotakCari = document.getElementById('audio-search');
  var pilihSemua = document.getElementById('audio-select-all');
  var bilahPilih = document.getElementById('selection-bar');
  var jumlahPilih = document.getElementById('selection-count');
  var tombolKunciMassal = document.getElementById('lock-items-button');
  var tombolLepasMassal = document.getElementById('unlock-items-button');

  if (!audio) {
    return;
  }

  var daftar = [];
  var indeks = -1;
  var trekAktif = null;

  function formatWaktu(detik) {
    if (isNaN(detik) || detik < 0) return '0:00';
    var m = Math.floor(detik / 60);
    var s = Math.floor(detik % 60);
    return m + ':' + (s < 10 ? '0' : '') + s;
  }

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

  function teksPutar(aktif) {
    if (!tombolPutar) {
      return;
    }
    var ikonPlay = tombolPutar.querySelector('.audio-icon-play');
    var ikonPause = tombolPutar.querySelector('.audio-icon-pause');
    if (ikonPlay && ikonPause) {
      ikonPlay.hidden = aktif;
      ikonPause.hidden = !aktif;
    }
    tombolPutar.setAttribute('data-playing', aktif ? 'true' : 'false');
  }

  function siapkanWinamp(kartu) {
    if (!formWinamp || !tombolWinamp) {
      return;
    }
    if (!kartu) {
      tombolWinamp.hidden = true;
      tombolWinamp.setAttribute('data-reauth-resource', '');
      return;
    }
    var id = kartu.getAttribute('data-file-id');
    formWinamp.action = '/media-vault/play/' + id;
    tombolWinamp.setAttribute('data-reauth-resource', id);
    tombolWinamp.hidden = false;
  }

  function putarKartu(kartu) {
    if (!kartu) {
      return;
    }
    var wadah = kartu.closest('[data-track-list]') || kartu.closest('tbody');
    daftar = wadah
      ? Array.prototype.slice.call(wadah.querySelectorAll('[data-track]:not([hidden])'))
      : [kartu];
    indeks = daftar.indexOf(kartu);

    if (trekAktif && trekAktif !== kartu) {
      trekAktif.classList.remove('is-playing');
    }
    trekAktif = kartu;
    kartu.classList.add('is-playing');

    var url = kartu.getAttribute('data-view-url');
    var nama = kartu.getAttribute('data-name') || pesan('no-track');

    if (judulBawah) judulBawah.textContent = nama;
    if (subBawah) subBawah.textContent = 'Audio';

    siapkanWinamp(kartu);
    if (!url) {
      return;
    }

    audio.src = url;
    audio.load();
    var janji = audio.play();
    if (janji && typeof janji.catch === 'function') {
      janji.catch(function () {});
    }
  }

  function geser(arah) {
    if (!daftar.length) {
      return;
    }
    indeks = (indeks + arah + daftar.length) % daftar.length;
    putarKartu(daftar[indeks]);
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
    }
  });

  document.addEventListener('change', function (event) {
    if (event.target.matches('[data-select-file]')) {
      perbaruiPilihan();
    }
  });

  // Kontrol tombol bar bawah
  if (tombolPutar) {
    tombolPutar.addEventListener('click', function () {
      if (!audio.src) {
        var pertama = document.querySelector('[data-track]:not([hidden])');
        if (pertama) putarKartu(pertama);
        return;
      }
      if (audio.paused) {
        audio.play().catch(function () {});
      } else {
        audio.pause();
      }
    });
  }

  if (tombolSebelum) {
    tombolSebelum.addEventListener('click', function () { geser(-1); });
  }
  if (tombolSesudah) {
    tombolSesudah.addEventListener('click', function () { geser(1); });
  }

  // Waktu dan progress bar
  audio.addEventListener('play', function () { teksPutar(true); });
  audio.addEventListener('pause', function () { teksPutar(false); });
  audio.addEventListener('ended', function () { geser(1); });
  audio.addEventListener('error', function () {
    if (audio.src) teksPutar(false);
  });

  audio.addEventListener('timeupdate', function () {
    if (waktuKini) waktuKini.textContent = formatWaktu(audio.currentTime);
    if (audio.duration && !isNaN(audio.duration)) {
      if (waktuTotal) waktuTotal.textContent = formatWaktu(audio.duration);
      if (isiKemajuan) {
        var pct = (audio.currentTime / audio.duration) * 100;
        isiKemajuan.style.width = pct + '%';
      }
    }
  });

  if (barKemajuan) {
    barKemajuan.addEventListener('click', function (e) {
      if (!audio.duration || isNaN(audio.duration)) return;
      var rect = barKemajuan.getBoundingClientRect();
      var rasio = (e.clientX - rect.left) / rect.width;
      audio.currentTime = rasio * audio.duration;
    });
  }

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

  // Hapus via KX.konfirmasiHapus
  document.addEventListener('submit', function (event) {
    var form = event.target;
    if (!form || !form.action || form.action.indexOf('/vault/delete/') === -1) {
      return;
    }
    if (form.getAttribute('data-kx-confirmed') === '1') {
      return;
    }

    event.preventDefault();
    var baris = form.closest('[data-track]');
    var namaItem = baris ? baris.getAttribute('data-name') : 'trek audio ini';

    if (window.KX && typeof window.KX.konfirmasiHapus === 'function') {
      window.KX.konfirmasiHapus({
        judul: 'Pindahkan ke Sampah?',
        nama: namaItem,
        pesan: 'Trek {nama} akan dipindahkan ke Sampah. Anda masih dapat memulihkannya dari sana.',
        labelTombol: 'Pindahkan',
        onKonfirmasi: function () {
          form.setAttribute('data-kx-confirmed', '1');
          form.submit();
        }
      });
    } else {
      if (window.confirm('Pindahkan ' + namaItem + ' ke Sampah?')) {
        form.setAttribute('data-kx-confirmed', '1');
        form.submit();
      }
    }
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
  teksPutar(false);
})();
