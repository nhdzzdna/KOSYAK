/**
 * static/js/secure_notes.js
 * ───────────────────────────
 * Membuka isi Secure Notes hanya setelah grant note.open (U2g):
 * - Daftar catatan ringkas: judul, tanggal, tombol Buka dan Hapus berdampingan (8px).
 * - Tombol Buka meminta grant note.open, mengambil isi catatan, lalu menampilkannya
 *   di dalam kartu/baris yang sama dengan tombol Tutup.
 * - Tombol Tutup menyembunyikan isi dan membersihkan teks dari DOM.
 * - Hapus dengan grant item.delete (pindah ke Sampah).
 * - Pencarian catatan lokal sisi klien via #sn-cari.
 */
(function () {
  'use strict';

  var akar = document.querySelector('.kx-sn-page');
  if (!akar) {
    return;
  }

  var cari = document.getElementById('sn-cari');
  var takCocok = document.getElementById('sn-tak-cocok');
  var daftar = document.getElementById('sn-daftar');

  function toast(teks, jenis) {
    if (window.KX && typeof KX.toast === 'function') {
      KX.toast(teks, jenis);
    }
  }

  function grantUntuk(scope, resource) {
    if (!window.CryptixReauth || typeof window.CryptixReauth.grantFor !== 'function') {
      return null;
    }
    return window.CryptixReauth.grantFor(scope, resource);
  }

  function mintaGrant(scope, resource) {
    return new Promise(function (selesai, tolak) {
      var penangan = function (event) {
        var detail = event.detail || {};
        if (detail.scope !== scope || String(detail.resource || '') !== String(resource || '')) {
          return;
        }
        document.removeEventListener('cryptix:reauth-grant', penangan);
        var token = detail.token || detail.grant;
        if (token) {
          selesai(token);
        } else {
          tolak(new Error('Catatan tidak dapat dibuka.'));
        }
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

  function bukaCatatan(baris, grant) {
    if (!baris) return;
    var id = baris.getAttribute('data-sn-item');
    var tombolBuka = baris.querySelector('[data-sn-buka]');
    var openUrl = tombolBuka ? tombolBuka.getAttribute('data-sn-open-url') : ('/secure-notes/open/' + id);

    var headers = { 'Content-Type': 'application/json' };
    if (grant) {
      headers['X-Reauth-Grant'] = grant;
    }

    apiFetch(openUrl, {
      method: 'POST',
      headers: headers,
      credentials: 'same-origin'
    }).then(function (resp) {
      return resp.json().catch(function () { return {}; }).then(function (data) {
        if (!resp.ok || !data.success) {
          throw new Error('Catatan tidak dapat dibuka.');
        }
        return data;
      });
    }).then(function (data) {
      var detail = baris.querySelector('[data-sn-detail]');
      if (!detail) return;

      var inputJudul = detail.querySelector('input[name="title"]');
      var inputIsi = detail.querySelector('textarea[name="content"]');

      if (inputJudul) {
        inputJudul.value = data.title == null ? '' : String(data.title);
      }
      if (inputIsi) {
        inputIsi.value = data.content == null ? '' : String(data.content);
      }

      detail.hidden = false;
      if (inputIsi) {
        inputIsi.focus();
      }
    }).catch(function (err) {
      toast('Catatan tidak dapat dibuka.', 'danger');
    });
  }

  function tutupCatatan(baris) {
    var detail = baris.querySelector('[data-sn-detail]');
    if (detail) {
      var inputIsi = detail.querySelector('textarea[name="content"]');
      if (inputIsi) {
        inputIsi.value = '';
      }
      detail.hidden = true;
    }
  }

  // ── Event klik: Buka & Tutup ──────────────────────────────────────────────
  document.addEventListener('click', function (event) {
    var btnBuka = event.target.closest('[data-sn-buka]');
    if (btnBuka) {
      var barisBuka = btnBuka.closest('[data-sn-item]');
      if (!barisBuka) return;

      var id = barisBuka.getAttribute('data-sn-item');
      var grant = grantUntuk('note.open', id);
      if (grant) {
        bukaCatatan(barisBuka, grant);
      } else {
        mintaGrant('note.open', id).then(function (token) {
          bukaCatatan(barisBuka, token);
        }).catch(function (err) {
          if (err && err.message) toast(err.message, 'danger');
        });
      }
      return;
    }

    var btnTutup = event.target.closest('[data-sn-tutup]');
    if (btnTutup) {
      var barisTutup = btnTutup.closest('[data-sn-item]');
      if (barisTutup) {
        tutupCatatan(barisTutup);
      }
      return;
    }
  });

  // ── Event listener untuk reauth callback ─────────────────────────────────
  document.addEventListener('cryptix:reauth-grant', function (event) {
    var detail = event.detail || {};
    if (detail.scope === 'note.open' && detail.resource) {
      var baris = document.querySelector('[data-sn-item="' + detail.resource + '"]');
      if (baris) {
        bukaCatatan(baris, detail.token || detail.grant);
      }
    }
  });

  // ── Pencarian catatan di sisi klien ──────────────────────────────────────
  if (cari) {
    cari.addEventListener('input', function () {
      var kueri = cari.value.trim().toLowerCase();
      var barisList = document.querySelectorAll('[data-sn-item]');
      var cocokAda = false;

      barisList.forEach(function (baris) {
        var judul = (baris.getAttribute('data-sn-judul') || '').toLowerCase();
        var cocok = !kueri || judul.indexOf(kueri) !== -1;
        baris.hidden = !cocok;
        if (cocok) cocokAda = true;
      });

      if (takCocok) {
        takCocok.hidden = barisList.length === 0 || cocokAda;
      }
    });
  }
})();
