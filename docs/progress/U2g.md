# U2g — Perbaikan UI dan Keamanan Lanjutan

## G1: Audio, Catatan, dan Teks Antarmuka

### Ringkasan

Sesi ini menyelesaikan perbaikan antarmuka dan penegakan gaya teks ringkas pada tiga area utama:
1. **Audio**: Memperbaiki tata letak tabel daftar dengan definisi `grid-template-columns` tunggal yang dipakai bersama oleh header dan setiap baris trek. Menghapus pemutar musik kustom di bilah bawah (bottom player bar) beserta kontrol lagu, waktu, dan progres bar kustom. Menggantinya dengan dialog modal berbasis `KX.modal` yang memuat elemen `<audio controls>` native peramban, di mana menutup modal menghentikan pemutaran dan melepas sumber media. Menghapus teks badge Winamp dan membersihkan keterangan dropzone.
2. **Catatan (Secure Notes)**: Menghilangkan struktur kartu editor ganda dan kotak biru penjelas. Mengubah daftar catatan menjadi daftar ringkas di mana setiap baris memuat judul, tanggal pembaruan, serta tombol Buka dan Hapus berdampingan dengan jarak persis 8px. Setelah verifikasi grant `note.open`, isi catatan dimuat dan ditampilkan di dalam kartu baris yang sama dengan tombol Tutup (yang membersihkan isi dari DOM saat ditutup). Form tambah catatan dipisahkan secara tetap di panel samping.
3. **Sapuan Teks Antarmuka**: Menerapkan aturan gaya teks singkat dan lugas di seluruh aplikasi. Menghapus seluruh kalimat penjelas, petunjuk berlebih, infobox redundant, dan penegasan yang dilarang (seperti "Bukan kata sandi akun Anda", "Berkas dienkripsi sebelum disimpan", dan "Isi catatan hanya tampil setelah verifikasi ulang"). Tetap mempertahankan label, placeholder, pesan galat, batas format dan ukuran berkas, peringatan tindakan permanen, serta keterbatasan jujur.

---

### A. Audio

Berkas: `templates/musik.html`, `static/js/musik.js`, `static/css/halaman/audio.css`.

1. **Perbaikan Tabel**:
   - Kolom header dan baris data kini berbagi deklarasi CSS Grid yang sama:
     `.kx-audio-table thead tr, .kx-audio-tr { display: grid; grid-template-columns: 40px 44px minmax(0, 1fr) 80px 110px 44px; align-items: center; }`
   - Enam kolom tertata sejajar: (1) kotak centang, (2) tombol putar bulat, (3) judul dengan badge ekstensi format, (4) durasi, (5) status badge, (6) menu aksi ⋯.
   - Responsif 3 lebar:
     - Desktop (>900px): 6 kolom lengkap (`40px 44px minmax(0, 1fr) 80px 110px 44px`).
     - Tablet (≤900px): tata letak form samping dan daftar bertumpuk 1 kolom, kolom tabel disesuaikan (`36px 40px minmax(0, 1fr) 70px 100px 40px`).
     - Ponsel (≤640px): kolom durasi dan status disembunyikan secara bersih, menyisakan 4 kolom (`36px 36px minmax(0, 1fr) 36px`) tanpa pembungkusan canggung.
   - Judul trek yang panjang dipotong dengan ellipsis (`overflow: hidden; text-overflow: ellipsis; white-space: nowrap;`), bukan dibungkus ke tengah baris.
   - Menghilangkan `overflow: auto` dan border dobel per cell yang sebelumnya menyebabkan garis horizontal nyasar di sebelah kanan kartu.
2. **Penghapusan Pemutar Bergaya Lagu**:
   - Menghapus elemen HTML pemutar bottom bar (`.kx-audio-player-bar`), sampul cover, tombol prev/next, tombol play besar, progress bar, pengatur volume, waktu berjalan, dan putar otomatis.
   - Menghapus aturan CSS terkait pemutar bottom bar di `audio.css`.
   - Menghapus `padding-bottom: 112px` pada `.kx-audio-page` yang sebelumnya dialokasikan untuk pemutar bawah.
   - Membersihkan fungsi JS dan event listener pemutar lama di `static/js/musik.js` (`geser`, `teksPutar`, listener `timeupdate`, listener klik progress bar).
3. **Modal Pemutar Audio Bawaan Browser**:
   - Tombol Putar pada baris trek membuka `#audio-modal` berbasis `KX.modal` yang berisi judul trek dan elemen `<audio id="music-audio" controls>` native peramban tanpa kontrol kustom.
   - Menutup modal (melalui tombol Tutup [data-kx-tutup], klik di luar overlay, penekanan tombol Escape, atau API `KX.modal.tutup`) memicu fungsi `hentikanAudio()`: menghentikan pemutaran (`audio.pause()`), melepas sumber (`audio.removeAttribute('src')`), dan memuat ulang (`audio.load()`).
   - Alur verifikasi ulang (`CryptixLock` dengan scope `item.view`) untuk trek terkunci tetap dipertahankan sebelum pemutaran diizinkan.
4. **Pembersihan Teks Audio**:
   - Menghapus teks dan elemen badge "Winamp terdeteksi di sistem" (`.kx-audio-winamp-badge`). Aksi "Buka di Winamp" tetap tersedia di menu titik tiga per item bila Winamp terpasang.
   - Menghapus frasa "· Berkas dienkripsi sebelum disimpan" dari petunjuk dropzone audio, menyisakan batas format dan ukuran: "MP3, WAV, FLAC, OGG, M4A · Maks. 64 MB".
5. **Fitur yang Dipertahankan**:
   - Kunci dan Lepas kunci per item lewat menu ⋯ dan massal via bar aksi mengambang.
   - Pindahkan ke Sampah via `KX.konfirmasiHapus`.
   - Penyaringan trek lokal secara langsung via kolom "Cari trek".
   - Dropzone berkas audio.
   - Bar aksi mengambang sinkron dengan kotak centang.

---

### B. Catatan (Secure Notes)

Berkas: `templates/secure_notes.html`, `static/js/secure_notes.js`, `static/css/halaman/secure_notes.css`.

1. **Struktur Daftar Ringkas**:
   - Setiap catatan ditampilkan dalam satu baris ringkas yang memuat:
     - Judul catatan (`.kx-sn-judul`) dengan pemotongan ellipsis.
     - Tanggal pembaruan (`.kx-sn-tanggal`).
     - Wadah aksi (`.kx-sn-aksi`) berisi tombol Buka dan tombol Hapus berdampingan dengan jarak persis 8px (`gap: var(--kx-space-2)`).
2. **Penghapusan Kotak Biru dan Penjelas**:
   - Menghapus kotak biru infobox (`#sn-buka-kotak`, `.kx-infobox`) beserta ikon gembok dan kalimat penjelas "Isi catatan hanya tampil setelah verifikasi ulang." (`MSG.NOTES_OPEN_HINT`).
3. **Pemuatan Isi Catatan Inline**:
   - Tombol Buka memiliki atribut `data-reauth="note.open"`.
   - Setelah verifikasi ulang berhasil, isi catatan dimuat via POST `/secure-notes/open/<id>` dengan header `X-Reauth-Grant` dan ditampilkan di dalam kartu baris yang sama pada kontainer `[data-sn-detail]`.
   - Menampilkan formulir edit catatan lengkap dengan tombol "Simpan" (dengan grant `note.edit`) dan tombol "Tutup".
   - Menekan tombol "Tutup" menyembunyikan detail dan mengosongkan nilai textarea di DOM agar teks rahasia tidak tertinggal di peramban.
4. **Panel Samping Form Tambah**:
   - Formulir tambah catatan baru ditempatkan secara tetap di panel samping (`<aside class="kx-card kx-sn-tambah">`).
   - Keadaan daftar kosong (`.kx-sn-kosong-lista`) hanya menampilkan pesan informatif "Belum ada catatan" tanpa tombol tambah duplikat yang berlebihan.

---

### C. Sapuan Teks Antarmuka

Daftar string penjelas/penegas yang dihapus per halaman:

| Halaman | Lokasi / Konstanta | Teks yang Dihapus | Alasan |
|---|---|---|---|
| **Crypto Tools** | `templates/crypto_tools.html` / `MSG.CRYPTO_KEY_HELP` | "Kunci untuk mengenkripsi dan mendekripsi pesan ini. Bukan kata sandi akun Anda." | Kalimat penjelas/penegas terlarang |
| **Crypto Tools** | `templates/crypto_tools.html` / `MSG.CRYPTO_KEY_HINT` | "Untuk cipher modern, teks diturunkan menjadi kunci 32 byte; 64 digit heksadesimal dipakai langsung." | Kalimat penjelas terlarang |
| **Crypto Tools** | `templates/crypto_tools.html` / `MSG.CRYPTO_SUPER_KEY_HINT` | "Kunci turunan untuk keempat layer diturunkan dengan PBKDF2-HMAC-SHA256 bersalt dari kunci rahasia ini." | Kalimat penjelas teknis terlarang |
| **Dokumen** | `templates/vault.html`, `templates/documents.html` / `MSG.DOC_DROPZONE_HINT` | " · Berkas dienkripsi sebelum disimpan" | Frasa penegas terlarang; dropzone hanya memuat format & ukuran |
| **Media** | `templates/media_vault.html` / `MSG.MEDIA_DROPZONE_HINT` | " · Berkas dienkripsi sebelum disimpan" | Frasa penegas terlarang; dropzone hanya memuat format & ukuran |
| **Audio** | `templates/musik.html` / `MSG.AUDIO_DROPZONE_HINT` | " · Berkas dienkripsi sebelum disimpan" | Frasa penegas terlarang; dropzone hanya memuat format & ukuran |
| **Audio** | `templates/musik.html` | "Winamp terdeteksi di sistem" | Teks penjelas badge audio |
| **Catatan** | `templates/secure_notes.html` / `MSG.NOTES_OPEN_HINT` | "Isi catatan hanya tampil setelah verifikasi ulang." | Kalimat penjelas terlarang |
| **Steganografi** | `templates/steganography.html` / `MSG.STEGO_ACCOUNT_KEY_NOTE` | "Muatan dienkripsi dengan kunci akun Anda dan hanya dapat diekstrak oleh akun ini." | Kalimat penjelas/penegas |
| **Steganografi** | `templates/steganography.html` / `MSG.STEGO_KEY_NOT_STORED` | "Kunci rahasia tidak disimpan di sistem." | Kalimat penegas |
| **Registrasi** | `templates/register.html` / `MSG.AUTH_DONGLE_REGISTER_HINT` | "Token keamanan ditulis ke dongle terpilih dan menjadi kunci fisik untuk membuka brankas. Pendaftaran ditolak bila tidak ada dongle yang terpasang." | Paragraf penjelas panjang |
| **Pemulihan** | `templates/account_recovery.html` / `MSG.AUTH_RECOVERY_INTRO` | "Gunakan kunci pemulihan bila dongle hilang atau rusak, atau bila lupa kata sandi. Kunci pemulihan tidak dapat dipulihkan jika hilang." | Infobox penjelas umum |
| **Pemulihan** | `templates/account_recovery.html` / `MSG.AUTH_RECOVERY_KEY_HINT` | "Salin kunci persis seperti saat ditampilkan, termasuk tanda hubung." | Petunjuk pengisian input |
| **Pemulihan** | `templates/account_recovery.html` / `MSG.AUTH_RECOVERY_DONGLE_HINT` | "Colokkan dongle baru, lalu muat ulang halaman ini bila daftar belum muncul." | Petunjuk pengisian input |
| **Settings** | `templates/settings.html` | "Diperlukan untuk membungkus ulang kunci data dengan dongle baru." | Keterangan penjelas input password |
| **Settings** | `templates/settings.html` / `MSG.USB_REREGISTER_HINT` | "Colokkan dongle baru lalu klik Refresh jika daftar drive kosong." | Petunjuk form |
| **Settings** | `templates/settings.html` / `MSG.SETTINGS_WEBAUTHN_NOTE` | "Gunakan autentikator platform bawaan perangkat (misalnya Windows Hello, Touch ID, atau kunci keamanan FIDO2) untuk verifikasi cepat." | Keterangan penjelas WebAuthn |
| **Dashboard** | `templates/dashboard.html` / `MSG.DASH_ACTIVITY_EMPTY_TEXT` | "Setiap unggahan dan peristiwa keamanan akan tercatat di sini." | Kalimat penjelas di empty state |
| **Security Center** | `templates/security_center.html` / `MSG.SC_ASSETS_EMPTY_TEXT` | "Seluruh dokumen, kredensial, catatan, dan gambar stego Anda akan diperiksa saat verifikasi." | Kalimat penjelas di empty state |
| **Security Center** | `templates/security_center.html` / `MSG.SC_LOG_EMPTY_TEXT` | "Aksi enkripsi, dekripsi, dan perubahan data Anda akan tercatat di sini." | Kalimat penjelas di empty state |

String yang **dipertahankan**:
- Batas format & ukuran dropzone (misal: "PDF, DOC, DOCX, XLS, XLSX, PPT, PPTX, TXT · Maks. 64 MB", "PNG, JPG, atau BMP · maks 4000 × 4000 piksel").
- Batasan format kata sandi (`AUTH_PASSWORD_HINT`, format minimal 12 karakter dan kombinasi karakter).
- Batasan format kunci Vigenere (`CRYPTO_VIGENERE_KEY_HINT`: "Kunci hanya boleh huruf A-Z.").
- Peringatan tindakan tidak dapat dibatalkan (Hapus permanen sampah `TRASH_ACTION_PURGE_MSG`, kosongkan sampah `TRASH_ACTION_EMPTY_MSG`, reset data `SETTINGS_DANGER_CONSEQUENCE_RESET`, hapus akun `SETTINGS_DANGER_CONSEQUENCE_DELETE`).
- Keterbatasan jujur akibat reset akun tanpa dongle / kata sandi (`RECOVERY_RESET_LIMITATION`).

---

### Tes yang Dihapus atau Diubah

Sesuai Aturan 6, seluruh penyesuaian tes dicatat secara eksplisit:

1. `tests/test_u2b_audio.py::test_halaman_audio_markup_kx`:
   - **Perubahan**: Mengganti asersi keberadaan pemutar kustom bawah (`kx-audio-player-bar`, `music-play-toggle`, `music-progress-bar`, `music-time-cur`) dengan asersi keberadaan modal audio (`id="audio-modal"`), elemen `<audio id="music-audio" controls>`, dan memastikan kelas/elemen pemutar kustom tidak ada lagi.
   - **Alasan**: Pemutar musik bawah bergaya lagu sengaja dihapus dan digantikan oleh modal pemutar bawaan browser per instruksi A.2 dan A.3.
2. `tests/test_u3_ui.py::TestSecureNotes::test_kosong_dengan_empty_state_editor`:
   - **Perubahan**: Menghapus asersi `"Belum ada catatan dipilih"`, `"data-sn-baru"`, dan `'id="sn-editor-isi" hidden'`. Mempertahankan asersi keberadaan form tambah di panel samping dan teks kosong "Belum ada catatan".
   - **Alasan**: Desain kartu editor ganda dan tombol tambah berlebih di empty state digantikan oleh formulir tambah tetap di samping.
3. `tests/test_u3_ui.py::TestSecureNotes::test_baris_dengan_grant_buka`:
   - **Perubahan**: Mengganti asersi penanda selektor baris lama menjadi `data-sn-item`, memastikan keberadaan tombol `id="sn-buka"` dan `id="sn-hapus-btn"`, serta memastikan kalimat penjelas "Isi catatan hanya tampil setelah verifikasi ulang." tidak ada.
   - **Alasan**: Penyesuaian terhadap struktur baris ringkas di mana tombol Buka dan Hapus berada berdampingan di setiap baris catatan.
4. `tests/test_u3_ui.py::TestSteganography::test_dua_kartu_dan_kontrak_sisip_ekstrak`:
   - **Perubahan**: Menghapus asersi keberadaan teks `MSG.STEGO_ACCOUNT_KEY_NOTE` dan `#sg-kunci-akun-info`.
   - **Alasan**: Teks penjelas tersebut sengaja dibuang pada sapuan gaya teks.
5. `tests/test_crypto_routes.py::TestCryptoToolsForm::test_form_contains_csrf_and_stages_option`:
   - **Perubahan**: Mengubah asersi `"Bukan kata sandi akun Anda." in body` menjadi `"Bukan kata sandi akun Anda." not in body`.
   - **Alasan**: Teks `CRYPTO_KEY_HELP` wajib dibuang sesuai instruksi C.
6. `tests/test_crypto_routes.py::TestCryptoToolsForm::test_hint_vigenere_dan_pbkdf2_tersembunyi_bawaan`:
   - **Perubahan**: Mengubah asersi `data-hint-kunci` tersembunyi menjadi memastikan atribut `data-hint-kunci` tidak ada di markup.
   - **Alasan**: Teks `CRYPTO_KEY_HINT` dihapus dari template.
7. `tests/test_settings.py::TestHalamanSettings::test_menampilkan_pilihan_dongle_dari_daftar_drive`:
   - **Perubahan**: Mengubah asersi `MSG.USB_REREGISTER_HINT in body` menjadi `MSG.USB_REREGISTER_HINT not in body`.
   - **Alasan**: Petunjuk `USB_REREGISTER_HINT` dihapus pada sapuan gaya teks.
8. **Tes Kontrak Baru** (`tests/test_u2g_kontrak.py`):
   - `test_kontrak_grid_header_dan_baris_audio`: Memeriksa bahwa `.kx-audio-table thead tr` dan `.kx-audio-tr` menggunakan deklarasi CSS Grid bersama.
   - `test_kontrak_tanpa_pemutar_kustom_di_musik_html`: Memeriksa bahwa elemen pemutar kustom (`kx-audio-player-bar`, dsb.) tidak ada di `templates/musik.html`.
   - `test_kontrak_modal_audio_controls`: Memeriksa keberadaan modal dengan tag `<audio controls>`.
   - `test_kontrak_catatan_tanpa_kotak_biru`: Memeriksa bahwa kartu catatan tidak memuat kotak biru (`sn-buka-kotak`) dan kalimat penjelas, serta tombol Buka & Hapus berdampingan.
   - `test_kontrak_string_terlarang_tidak_ada`: Memeriksa bahwa seluruh 6 string terlarang tidak muncul di seluruh berkas template maupun `modules/strings.py`.

---

### Riwayat Commit G1

| Commit | Pesan Commit | Deskripsi |
|---|---|---|
| `67207b8` | `[U2g] audio tabel dan modal` | Perbaikan tabel audio grid bersama 6 kolom, modal audio controls native, penghapusan pemutar bottom bar |
| `ed005f7` | `[U2g] catatan` | Daftar catatan ringkas satu baris (Buka & Hapus 8px), hapus kotak biru, detail inline, form samping |
| `db2ec69` | `[U2g] teks antarmuka` | Sapuan gaya teks lugas di 12 berkas template dan strings.py sesuai aturan |
| (commit penutup) | `[U2g] tes dan dokumen g1` | Pembaruan tes yang disesuaikan, tes kontrak baru test_u2g_kontrak.py, dokumen U2g.md |
