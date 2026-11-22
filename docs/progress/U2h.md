# U2h — Perbaikan Audio, Catatan, dan Teks Verifikasi

## Ringkasan Eksekutif

Sesi ini menyelesaikan lima bagian perbaikan terpadu (Bagian A sampai E) pada branch `u2h-perbaikan`:
1. **Bagian A (Tabel Audio Tidak Sejajar)**: Mengganti deklarasi CSS grid per baris pada tabel Audio dengan tabel HTML standar `<table class="kx-table">` yang memanfaatkan `<colgroup>` dan `table-layout: fixed`. Menghilangkan bingkai dan latar kartu ganda pada baris trek.
2. **Bagian B (Audio Tidak Bisa Diputar)**: Memperbaiki kebijakan keamanan CSP pada `app.py` dengan menambahkan sumber `blob:` pada direktif `media-src`. Memperkuat klien `static/js/musik.js` dalam mengonstruksi Blob audio dengan penentuan MIME type yang tepat serta penanganan galat pemutaran dan pelepasan Blob URL.
3. **Bagian C (Hapus Opsi Kunci di Audio)**: Menghilangkan opsi "Kunci" dan "Lepas kunci" per item, tombol kunci massal di bar aksi mengambang, serta kolom Status dan badge "Terkunci" pada antarmuka Audio.
4. **Bagian D (Catatan Tidak Bisa Dibuka Setelah Verifikasi)**: Memperbaiki bug pada `static/js/secure_notes.js` yang sebelumnya membaca properti `detail.grant` (bernilai `undefined`), kini membaca `detail.token || detail.grant` sehingga token grant yang valid dikirimkan ke endpoint `/secure-notes/open/<id>`.
5. **Bagian E (Teks Teknis yang Bocor ke Antarmuka)**: Menggantikan teks teknis reauth yang membocorkan scope bertitik dan ID numerik ("Tindakan '...' pada sumber daya ...") dengan pemetaan kalimat ramah pengguna yang ringkas di `modules/strings.py` (`REAUTH_SCOPE_LABELS`), serta membersihkan kata "grant", "scope", dan "sumber daya" dari string antarmuka pengguna.

---

## Rincian Per Bagian

### Bagian A: Tabel Audio Tidak Sejajar
- **Penyebab**: Baris tabel menggunakan `display: grid` pada elemen `tr` dengan padding dan margin tersendiri di dalam kartu tabel, menghasilkan bingkai ganda (kartu di dalam kartu) dan ketidaksejajaran sel kolom header dengan baris data.
- **Perbaikan**:
  - Mengubah tabel menjadi tabel native dengan `table-layout: fixed` dan `<colgroup>`.
  - Mengatur lebar kolom satu kali pada `<colgroup>` yang dipakai bersama oleh `<thead>` dan `<tbody>`.
  - Menghilangkan `border`, `border-radius`, dan margin kartu pada `.kx-audio-tr`.
  - Menerapkan pemotongan teks judul panjang dengan `ellipsis`.
  - Menerapkan responsivitas: menyembunyikan kolom Durasi pada tablet (<=900px) dan ponsel (<=640px) pada level `<col>`, `<th>`, dan `<td>` secara serentak.
- **Keterbatasan Visual**: Pustaka otomasi peramban headless (Playwright) tidak terpasang di lingkungan sistem, sehingga perhitungan selisih piksel posisi `x` kiri antar sel belum diverifikasi secara visual otomatis, namun telah diuji keselarasan DOM dan kontrak CSS-nya.

### Bagian B: Audio Tidak Bisa Diputar
- **Penyebab**: Direktif CSP `media-src 'self'` di `app.py` memblokir pemuatan URL `blob:` yang dibuat oleh klien JavaScript saat memutar audio hasil unduhan stream terenkripsi.
- **Perbaikan**:
  - Menambahkan `blob:` secara sempit hanya pada direktif `media-src` di `app.py` (`media-src 'self' blob:;`).
  - Memperbarui pengujian CSP di `tests/test_headers_csp.py`.
  - Memperkuat klien `static/js/musik.js` untuk membentuk `Blob` dengan tipe MIME dari header respons `Content-Type` (atau fallback ekstensi), memanggil `audio.load()` dan `audio.play()`, menangani event `error` pada elemen `<audio>` dan kegagalan `fetch` dengan toast bahaya ("Audio tidak dapat diputar."), serta membebaskan Blob URL saat modal ditutup.
  - Memverifikasi endpoint server `/media-vault/stream/<id>` mengembalikan status 200, tipe konten `audio/*`, serta isi dan panjang byte yang sesuai dengan plaintext asli.

### Bagian C: Hapus Opsi Kunci di Audio
- **Penyebab**: Karena pemutaran audio kini selalu mewajibkan verifikasi step-up `audio.play` setiap kali diputar, fitur kunci item menjadi redundan di Audio. Kolom Status juga selalu berisi "Terenkripsi".
- **Perbaikan**:
  - Menghapus tombol menu "Kunci" dan "Lepas kunci" per item pada baris trek di `templates/musik.html`.
  - Menghapus tombol kunci dan lepas kunci massal pada bar aksi mengambang (`templates/musik.html`).
  - Menghapus kolom Status secara serentak di `<colgroup>`, `<thead>`, dan `<tbody>` agar tabel tetap sejajar dengan 5 kolom.
  - Menghapus fungsi JS terkait penguncian audio di `static/js/musik.js` (`kunciKartu`, `lepasKunciKartu`, `aksiMassal`, `ubahStatus`, dsb.).
  - Menghapus kelas CSS terkait kolom status dan lencana terkunci di `static/css/halaman/audio.css`.

### Bagian D: Catatan Tidak Bisa Dibuka Setelah Verifikasi
- **Penyebab**: Pada `static/js/secure_notes.js`, penangan event `cryptix:reauth-grant` membaca `detail.grant`. Objek detail dari `reauth.js` menyediakan token pada properti `detail.token`. Akibatnya, `detail.grant` bernilai `undefined`, permintaan `POST /secure-notes/open/<id>` dikirim tanpa header `X-Reauth-Grant`, dan server menolak dengan HTTP 401.
- **Perbaikan**:
  - Memperbaiki pembacaan token pada penangan event menjadi `detail.token || detail.grant`.
  - Menampilkan toast kesalahan singkat `"Catatan tidak dapat dibuka."` saat permintaan gagal.
  - Mengonfirmasi seluruh selektor data-* dan id yang dirujuk oleh `secure_notes.js` cocok dengan `templates/secure_notes.html`.
  - Memastikan wadah detail tidak memiliki hidden permanen (`display: none !important`).
  - Memeriksa halaman lain yang memakai verifikasi (`account_vault.js`, `dokumen.js`, `steganography.js`, `sampah.js`): semuanya telah menggunakan `detail.token` dengan benar.

### Bagian E: Teks Teknis yang Bocor ke Antarmuka
- **Penyebab**: Teks konteks modal reauth sebelumnya dibentuk secara dinamis dengan merangkai nama scope dan resource ID internal (`Tindakan "{scope}" pada sumber daya {resource} memerlukan verifikasi...`). Selain itu, beberapa string galat default memuat kata "grant", "scope", dan "sumber daya".
- **Perbaikan**:
  - Menambahkan kamus `REAUTH_SCOPE_LABELS` dan konstanta `REAUTH_DEFAULT_LABEL` di `modules/strings.py` yang memetakan scope ke kalimat ramah pengguna yang lugas tanpa istilah internal.
  - Memperbarui `templates/_reauth_modal.html` untuk meneruskan kamus label dalam atribut `data-labels` (JSON).
  - Memperbarui `static/js/reauth.js` untuk membaca label dari atribut modal atau kamus internal dan menampilkannya pada `#reauth-context`.
  - Menyapu `modules/strings.py` untuk mengganti kata teknis:
    - `REAUTH_INVALID`: `"Grant autentikasi ulang tidak valid..."` -> `"Verifikasi tidak valid atau sudah kedaluwarsa."`
    - `REAUTH_SESSION_MISMATCH`: `"Grant autentikasi ulang ini milik sesi lain."` -> `"Verifikasi ini milik sesi lain."`
    - `REAUTH_SCOPE_MISMATCH`: `"Grant tidak berlaku untuk tindakan ini."` -> `"Verifikasi tidak berlaku untuk tindakan ini."`
    - `REAUTH_RESOURCE_MISMATCH`: `"Grant tidak berlaku untuk sumber daya ini."` -> `"Verifikasi tidak berlaku untuk item ini."`
    - `REAUTH_SCOPE_UNKNOWN`: `"Scope autentikasi ulang tidak dikenal."` -> `"Jenis tindakan tidak dikenal."`
    - `ERROR_UNAUTHORIZED`: `"Silakan masuk terlebih dahulu untuk mengakses sumber daya ini."` -> `"Silakan masuk terlebih dahulu."`
    - `ERROR_FORBIDDEN`: `"Anda tidak memiliki izin untuk mengakses sumber daya ini."` -> `"Akses ditolak."`
    - `ERROR_NOT_FOUND`: `"Halaman atau sumber daya yang Anda minta tidak ditemukan."` -> `"Halaman yang Anda minta tidak ditemukan."`
    - `ERROR_METHOD_NOT_ALLOWED`: `"Metode permintaan tidak diizinkan untuk sumber daya ini."` -> `"Metode permintaan tidak diizinkan."`

---

## Daftar Tes yang Diubah atau Dihapus

1. `tests/test_u2g_kontrak.py::test_kontrak_grid_header_dan_baris_audio`:
   - **Perubahan**: Diganti menjadi `test_kontrak_tabel_audio_fixed_dan_colgroup` untuk memastikan tabel menggunakan `<colgroup>`, `table-layout: fixed`, tanpa `display: grid` pada `tr`, dan jumlah `<th>` sama dengan `<td>`.
   - **Alasan**: Markup tabel diubah dari CSS Grid per baris ke tabel fixed native per Bagian A.
2. `tests/test_headers_csp.py`:
   - **Perubahan**: Konstanta `CSP` dan fungsi `_periksa_header` disesuaikan untuk menguji keberadaan `media-src 'self' blob:;`.
   - **Alasan**: Kebijakan CSP diperbarui pada `app.py` per Bagian B.
3. `tests/test_u2b_audio.py::test_halaman_audio_markup_kx`:
   - **Perubahan**: Menghapus asersi `'Terenkripsi' in html`, digantikan dengan asersi `'Terenkripsi' not in html` dan `'kx-audio-cell-status' not in html`.
   - **Alasan**: Kolom status sengaja dihapus dari antarmuka Audio per Bagian C.
4. `tests/test_u2b_audio.py::test_halaman_audio_status_terkunci`:
   - **Perubahan**: Mengubah asersi badge `"Terkunci"` dan `data-locked="1"` menjadi asersi ketiadaan badge dan menu kunci (`assert "Terkunci" not in html`, `assert "data-track-lock" not in html`).
   - **Alasan**: Fitur kunci dan status dihapus dari Audio per Bagian C.
5. `tests/test_u2f_media_audio.py::test_audio_tanpa_ui_folder`:
   - **Perubahan**: Mengubah `assert "data-track-lock" in html` menjadi `assert "data-track-lock" not in html`.
   - **Alasan**: Menu penguncian audio sengaja dihapus per Bagian C.
6. `tests/test_u2f_media_audio.py::test_audio_trek_terkunci_tampil_dan_bisa_dilepas`:
   - **Perubahan**: Mengubah asersi menu lepas kunci dan badge terkunci menjadi memastikan menu dan badge tersebut tidak ada di HTML.
   - **Alasan**: Penyesuaian ketiadaan opsi kunci di Audio per Bagian C.
7. `tests/test_n3b_musik_dokumen.py::TestDaftarSemuaDanFolderTerbuka::test_item_terkunci_tetap_tampil_di_semua_audio`:
   - **Perubahan**: Mengubah `assert "Terkunci" in semua` menjadi `assert "Terkunci" not in semua`, sambil tetap mempertahankan asersi keberadaan item `assert "kunci-luar.mp3" in semua`.
   - **Alasan**: Kolom Status dan badge "Terkunci" sengaja dihapus dari antarmuka Audio per Bagian C.
8. **Penambahan Tes Kontrak Baru** (`tests/test_u2g_kontrak.py`):
   - `test_server_buka_catatan_dengan_grant`: Menguji endpoint `/secure-notes/open/<id>` dengan grant `note.open` (200), tanpa grant (401), dan scope salah (403).
   - `test_kontrak_selektor_secure_notes_js`: Menguji bahwa seluruh selektor JS ada pada template dan kontainer detail tidak memiliki `display: none !important`.
   - `test_kontrak_pemetaan_label_verifikasi`: Menguji kamus label verifikasi bebas nama scope bertitik dan kata terlarang.
   - `test_kontrak_modal_reauth_tanpa_nama_scope_mentah`: Menguji bahwa render modal reauth tidak membocorkan nama scope mentah.

