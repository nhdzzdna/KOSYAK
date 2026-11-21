# U2f — Perbaikan UI Lanjutan (F1)

## F1 Media dan Audio

### Ringkasan

Perbaikan ini menutup dua kejanggalan antarmuka: bagian "Semua" pada Media
yang masih menampilkan item album, serta ganti nama album/berkas yang tidak
berfungsi. Halaman Audio dibersihkan dari seluruh fitur folder sehingga
menjadi daftar satu tingkat, lalu tata letaknya dirapikan mengikuti pola
halaman Media dan Dokumen. Backend, rute, grant, dan alur kriptografi tidak
diubah.

### Media

- "Semua" kini hanya memuat media yang tidak berada di album mana pun.
  Bagian "Tanpa album" beserta chip/markup, JS, dan tesnya dihapus karena
  menjadi duplikat.
- Pemindahan media ke album menghapus kartu dari "Semua" tanpa memuat ulang
  halaman. Pemindahan keluar album mengembalikan kartu ke "Semua" dan
  membuat grid "Semua" bila sebelumnya kosong.
- Isi album terkunci tetap tidak dimuat tanpa grant `album.unlock`; server
  tetap menolak dengan 403 beralasan `terkunci`.
- Tombol `#album-rename` membuka `#album-rename-form`, mengisi input dengan
  nama album saat ini, lalu mengirim `POST /api/collections/<id>/rename`.
  Judul album, kartu album, dan nama pada atribut `data-*` diperbarui tanpa
  memuat ulang. Keberhasilan dan kegagalan dilaporkan lewat `KX.toast`.
- Penampil media memiliki `#viewer-rename` dan `#viewer-rename-form` yang
  tersembunyi saat awal. Berkas diganti nama lewat
  `POST /api/media/<id>/rename`, lalu judul penampil dan nama kartu
  diperbarui.
- Ganti nama folder Dokumen (`#folder-rename`) diperiksa dan diperbaiki
  dengan pola yang sama: form tersembunyi saat awal, memakai endpoint
  `/rename`, memperbarui judul dan kartu folder tanpa memuat ulang, dan
  memakai toast.

### Audio

- Seluruh UI folder dihapus: panel folder, chip folder, "+ Folder baru",
  kunci folder, pindahkan ke folder, ganti nama folder, badge folder, dan
  aksi massal khusus folder. Rute dan backend folder tidak dihapus.
- Halaman Audio menjadi daftar satu tingkat: dropzone, kolom "Cari trek",
  daftar trek, dan pemutar bawah.
- Daftar memuat semua audio di luar koleksi (termasuk yang terkunci) serta
  isi koleksi terbuka. Isi koleksi terkunci tetap tidak dimuat tanpa grant.
- Aksi Kunci dan Lepas kunci tersedia per item lewat menu titik tiga serta
  untuk item terpilih lewat bar aksi mengambang. Lepas kunci memakai grant
  `item.unlock` dan `cryptix:reauth-grant` yang sudah ada.
- Logika stream, grant `item.view` untuk trek terkunci, Hapus ke Sampah
  melalui `KX.konfirmasiHapus`, dan Buka di Winamp dipertahankan.
- Jarak antarbagian diseragamkan menjadi 16px, kolom folder dihapus dari
  tabel, pemutar diberi ruang bawah agar daftar tidak tertutup, dan tata
  letak responsif tiga lebar dipertahankan.

### Keputusan

1. **Penyaringan di sisi tampilan, bukan backend.** Data "tanpa album" sudah
   tersedia dari `halaman_koleksi`; template Media memakai daftar itu dan
   pembaruan setelah pemindahan dilakukan di klien. Tidak ada perubahan
   perilaku rute.
2. **Daftar audio satu tingkat.** Karena panel folder dihapus, daftar tidak
   lagi memakai bagian "Semua" dan "Tanpa folder". Daftar dibentuk dari
   audio di luar koleksi ditambah isi koleksi terbuka agar isi folder
   terkunci tetap tersembunyi tanpa grant.
3. **Aksi folder yang tersisa.** Setelah pemindahan ke folder dihapus,
   bar aksi mengambang hanya memuat Kunci dan Lepas kunci. Logika keduanya
   dipindahkan ke `musik.js` karena `collection_folders.js` tidak lagi
   dimuat di halaman Audio.
4. **Tanpa token CSS baru.** Seluruh CSS halaman memakai token `--kx-*`
   yang sudah terdefinisi.

### Tes yang Dihapus atau Diubah

- Dihapus: `tests/test_u2b_audio.py::test_halaman_audio_badge_folder_di_semua`.
  Alasan: badge folder tidak lagi ada di antarmuka Audio.
- Diubah: `tests/test_u2b_media.py::test_halaman_media_badge_album_di_semua`
  menjadi `test_halaman_media_item_album_tidak_tampil_di_semua`. Alasan:
  item album tidak lagi tampil di "Semua", sehingga badge album di "Semua"
  tidak relevan.
- Diubah: `tests/test_n3b_musik_dokumen.py` pada kelas
  `TestDaftarSemuaDanFolderTerbuka`. Alasan: Audio tidak lagi memiliki
  bagian "Tanpa folder"; Media juga tidak lagi memiliki bagian tersebut.
  Bagian Dokumen tetap diuji.
- Diubah: `tests/test_n3b_musik_dokumen.py::TestFolderTerkunci::test_tanpa_grant_isi_tidak_dimuat`.
  Alasan: nama folder tidak lagi dirender di halaman Audio; pemeriksaan isi
  terkunci tetap dipertahankan.
- Diubah: `tests/test_ub_kunci.py` pada tiga tes yang bergantung pada item
  album muncul di "Semua" versi halaman. Alasan: aturan baru menempatkan
  item album hanya di dalam album; status dan grant tetap diperiksa lewat
  API album.
- Diubah: `tests/test_perbaikan_viewer_pratinjau.py::test_dropdown_media_tanpa_item_lihat`.
  Alasan: kartu media tidak lagi dirender ganda di "Semua" dan "Tanpa
  album", sehingga jumlah dropdown dan tombol buka menjadi separuh.

### Keterbatasan

- Verifikasi visual peramban tidak dijalankan pada lingkungan ini karena
  tidak tersedia peramban headless; tangkapan layar /audio sebelum dan
  sesudah tidak dapat dilampirkan.
- Tombol Lepas kunci massal dapat meminta autentikasi ulang lebih dari satu
  kali bila item terpilih berasal dari berkas berbeda yang bukan anggota
  koleksi.

### Hasil Tes

- Tes terarah Media, Audio, koleksi, kerangka, dan U2e: lihat ringkasan
  pytest pada laporan sesi.
- Suite penuh: dijalankan sekali di akhir sesi.

---

## F2 Account Vault

### Ringkasan

Penyempurnaan antarmuka Account Vault berfokus pada penghapusan tombol salin yang
tidak aman/berlebih dan penyeragaman kontrol lihat kata sandi dengan komponen mata
standar `KX.sandi` (`data-kx-sandi`). Alur grant autentikasi ulang `account.reveal`,
pembersihan otomatis 15 detik, dan struktur backend/database tetap dipertahankan.

### Perubahan Antarmuka dan Logika

- **Pembersihan Tombol Salin**:
  - Menghapus tombol "Salin" pada setiap baris kredensial (atribut `data-av-salin`).
  - Menghapus tombol salin di samping username dan kata sandi pada kotak tampilan reveal (atribut `data-copy-field`).
  - Menghapus fungsi dan penanganan event clipboard di `static/js/account_vault.js` (`salinKataSandi`, `salinKeClipboard`, timer clipboard 30 detik, serta pelacakan `niat`).
  - Menghapus string antarmuka `ACCOUNT_COPY_DONE` dan `ACCOUNT_COPY_FAILED` dari `modules/strings.py` dan atribut `data-msg-copy-*` dari template `templates/account_vault.html`.
- **Integrasi Toggle Mata Sandi**:
  - Menambahkan atribut `data-kx-sandi` pada kontainer kata sandi di kotak tampilan reveal (`kx-av-sandi`) dan pada form Edit (`kx-av-edit`).
  - Kontrol mata menggunakan generator tombol `KX.sandi` (`kx-sandi-toggle`), lengkap dengan `aria-label`, `aria-pressed`, ikon sprite tunggal (`eye` / `eye-off`), dan ring fokus keyboard yang terlihat.
  - Memperbarui `account_vault.js` agar me-reset status toggle sandi menjadi tersamar/tersembunyi (`type="password"`, `aria-pressed="false"`, ikon `eye-off`) setiap kali detail dibuka ulang, ditutup, atau dibersihkan otomatis setelah 15 detik.
- **Tata Letak & Jarak**:
  - Tombol aksi baris (`.kx-av-aksi`) dan tombol aksi reveal (`.kx-av-reveal-aksi`) memiliki jarak antartombol 8px (`gap: var(--kx-space-2)`), tidak menempel.

### Tes yang Dihapus atau Diubah

- Diperbarui: `tests/test_u3_ui.py::TestAccountVault::test_baris_dengan_detail_edit_dan_hapus`.
  - Ditambahkan asersi bahwa `data-av-salin`, `data-copy-field`, `data-msg-copy-done`, dan `data-msg-copy-failed` tidak ada pada halaman.
  - Ditambahkan asersi bahwa kontainer kata sandi pada detail reveal dan form edit memiliki komponen `data-kx-sandi`.
  - Memastikan seluruh halaman Account Vault bebas dari skrip inline maupun handler event inline.

### Keterbatasan

- Uji coba visual peramban (interaksi klik mata langsung di browser) dilakukan lewat pengujian DOM struktural dan unit test karena ketiadaan peramban headless GUI di lingkungan uji.

---

## F3 Crypto Tools

### Ringkasan

Perbaikan F3 menyelesaikan dua masalah pada halaman Crypto Tools:
1. **Pencegahan autofill kata sandi akun pada kolom kunci**: Browser sebelumnya mengabaikan `autocomplete="off"` pada input `type="password"` dan menganggap form ini sebagai formulir login, sehingga password manager otomatis mengisi kata sandi akun pengguna ke dalam kolom kunci.
2. **Fitur "Tampilkan tahapan" untuk setiap metode kriptografi**: Menambahkan fungsi penelusuran tahapan jejak proses di modul kriptografi (`modules/cryptography/`) untuk metode Vigenere, Playfair, ChaCha20, Blowfish-CBC, serta Super Encryption, baik untuk operasi enkripsi maupun dekripsi. Kartu tahapan hanya tampil saat kotak centang "Tampilkan tahapan" dicentang dan operasi berhasil menghasilkan keluaran.

### Masalah Kunci Terisi Kata Sandi Akun

- **Penyebab**: Browser dan pengelola kata sandi (password manager) menggunakan heuristik untuk mendeteksi form kredensial. Kolom `type="password"` dengan `autocomplete="off"` sering diabaikan oleh browser modern, menyebabkan password akun terisi otomatis ke dalam kolom kunci rahasia.
- **Solusi Sisi Klien**:
  - Mengubah `autocomplete="off"` menjadi `autocomplete="new-password"` pada kolom kunci dan kunci rahasia.
  - Menambahkan atribut proteksi autofill: atribut `readonly` saat inisialisasi yang dilepas otomatis pada event `focus` (`lepasReadonly`), `data-lpignore="true"`, `data-1p-ignore="true"`, dan `data-form-type="other"`.
  - Pada event `load`, skrip JS memastikan nilai input dikosongkan bila browser mencoba memaksakan autofill sebelum input difokuskan oleh pengguna.
  - Memperbarui label menjadi "Kunci enkripsi" (`MSG.CRYPTO_KEY_LABEL`) dengan teks bantuan jelas: "Kunci untuk mengenkripsi dan mendekripsi pesan ini. Bukan kata sandi akun Anda." (`MSG.CRYPTO_KEY_HELP`) lewat `modules/strings.py`.
  - Memastikan form berdiri sendiri dengan `autocomplete="off"` tanpa input username tersembunyi yang dapat memicu heuristik login.

### Fitur Tahapan Kriptografi Tiap Metode

- **Daftar Tahapan Per Metode**:
  - **Vigenere** (`classical_cipher_1.py`):
    - *Ditampilkan*: Teks input, hasil akhir, parameter panjang kunci dan siklus pengulangan kunci, serta tabel jejak per karakter (posisi, karakter asal, huruf kunci pembimbing, dan karakter hasil pergeseran).
    - *Disembunyikan*: String kunci utuh tidak diekspos di badge parameter untuk mencegah kebocoran kunci rahasia.
  - **Playfair** (`classical_cipher_2.py`):
    - *Ditampilkan*: Teks input, hasil akhir, representasi matriks 5×5 (J digabung dengan I), ringkasan aturan persiapan teks (huruf kembar/ganjil disisipkan X), serta tabel jejak pasangan digraf asal, pasangan hasil, dan aturan transformasi yang diterapkan (`baris sama`, `kolom sama`, `persegi`).
    - *Disembunyikan*: Kunci mentah yang diketik pengguna tidak diekspos.
  - **ChaCha20** (`modern_cipher_1.py`):
    - *Ditampilkan*: Nonce 16-byte (hex), mode operasi stream, ukuran data byte, ringkasan bahwa keystream dibangkitkan dari kunci dan nonce melalui 20 ronde ChaCha20 lalu di-XOR dengan byte masukan, serta tabel jejak byte heksadesimal sebelum dan sesudah.
    - *Disembunyikan*: Kunci mentah 32-byte tidak pernah dimasukkan ke parameter atau jejak.
  - **Blowfish-CBC** (`modern_cipher_2.py`):
    - *Ditampilkan*: IV 8-byte acak (hex), mode CBC, ukuran blok 8-byte, jumlah blok, skema padding PKCS#7 (panjang padding yang ditambahkan pada enkripsi atau dibuang pada dekripsi), serta jejak byte heksadesimal sebelum dan sesudah.
    - *Disembunyikan*: Kunci mentah tidak pernah diekspos.
  - **Super Encryption** (`super_encryption.py`):
    - *Ditampilkan*: Keempat layer berurutan (Vigenere → Playfair → ChaCha20 → Blowfish-CBC pada enkripsi, dan urutan terbalik pada dekripsi) dengan verifikasi MAC HMAC-SHA256. Jejak tiap layer dan nilai perantara aman (nonce, IV).
    - *Disembunyikan*: Kunci turunan tiap layer dan passphrase pengguna.
- **Kendali Checkbox & Keamanan Data**:
  - Checkbox "Tampilkan tahapan" (`name="show_stages"`, `id="ct-show-stages"`, nilai `1`) mengontrol pembuatan objek tahapan.
  - Jika checkbox tidak dicentang, `stages` bernilai `None` dan komponen kartu `kx-ct-tahapan` tidak dirender sama sekali.
  - Backend tidak menyimpan teks input, kunci, maupun tahapan proses ke dalam sesi, cookie, basis data, atau log server.

### Tes Baru dan Penyesuaian Tes

- **Tes Baru**:
  - `tests/test_crypto_stages_unit.py`: Menguji keselarasan keluaran fungsi tahapan baru (`vigenere_encrypt_stages`, `vigenere_decrypt_stages`, `playfair_encrypt_stages`, `playfair_decrypt_stages`, `chacha20_encrypt_stages`, `chacha20_decrypt_stages`, `blowfish_encrypt_stages`, `blowfish_decrypt_stages`) dengan fungsi enkripsi/dekripsi dasar, memastikan pemulihan teks asli secara roundtrip, serta memvalidasi ketiadaan kebocoran kunci mentah.
- **Penyesuaian Tes**:
  - `tests/test_crypto_routes.py::TestCryptoToolsForm::test_form_contains_csrf_and_stages_option`: Menggantikan pemeriksaan ketiadaan opsi tahapan lama (`show_steps not in body`) menjadi pemeriksaan keberadaan kontrol checkbox tahapan (`show_stages`), atribut proteksi autofill (`autocomplete="new-password"`, `readonly`, `data-lpignore="true"`), dan teks label/bantuan baru.
  - `tests/test_crypto_routes.py::TestSuperEncryptionRoute`: Memisahkan pengujian enkripsi dengan checkbox (`show_stages="1"`) yang menampilkan 4 layer, dan pengujian tanpa checkbox yang memastikan kartu tahapan tidak dirender.
  - `tests/test_crypto_routes.py::test_tabel_jejak_tunggal_tiap_cipher_dan_aksi`: Mengirimkan `show_stages="1"` untuk memverifikasi struktur tabel jejak pada tiap cipher dan aksi.
  - `tests/test_u3_ui.py::TestCryptoTools::test_lima_kartu_algoritma_dengan_deskripsi`: Diperbarui untuk memverifikasi keberadaan `name="show_stages"` dan teks "Tampilkan tahapan".
  - `tests/test_u3_ui.py::TestCryptoTools::test_hasil_dan_tahapan_setelah_proses`: Mengirimkan `show_stages="1"` untuk menguji kartu tahapan, serta ditambahkan `test_hasil_tanpa_tahapan_bila_checkbox_tidak_dicentang`.

### Keterbatasan

- Pengujian pencegahan autofill password manager diuji melalui verifikasi atribut DOM struktural dan simulasi event JS; perilaku ekstensi browser pihak ketiga tertentu di lingkungan nyata bergantung pada pengaturan heuristik masing-masing peramban.


