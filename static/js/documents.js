/**
 * static/js/documents.js
 * ──────────────────────
 * Skrip pendukung tampilan antarmuka dokumen (kx-doc-*).
 * Tidak inline (CSP ketat).
 * Menghubungkan KX.dropzone, konfirmasi hapus via modal, integrasi dengan
 * collection_folders.js dan dokumen.js.
 */
(function () {
  'use strict';

  // Sinkronisasi data-select-file dengan KX.aksiMengambang
  function sinkronPilihan() {
    var checkboxes = document.querySelectorAll('[data-select-file]');
    checkboxes.forEach(function (cb) {
      if (!cb.hasAttribute('data-kx-pilih')) {
        cb.setAttribute('data-kx-pilih', '');
      }
    });
    if (window.KX && window.KX.aksiMengambang) {
      window.KX.aksiMengambang.segarkan();
    }
  }

  // Amati penambahan item dinamis dari buka folder agar checkbox terdaftar
  document.addEventListener('collection:items-loaded', function () {
    sinkronPilihan();
  });

  // Inisialisasi awal saat dokumen siap
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', sinkronPilihan);
  } else {
    sinkronPilihan();
  }
})();

