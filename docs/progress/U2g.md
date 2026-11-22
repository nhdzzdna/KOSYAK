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

---

## G2: Verifikasi untuk Hapus, Pulihkan, dan Putar Audio

### Rancangan Arsitektur dan Scope (Ditulis Sebelum Pengkodean)

Berdasarkan audit terhadap `modules/authentication/reauth.py`, `routes/reauth_routes.py`, `routes/trash_routes.py`, `routes/media_routes.py`, `static/js/reauth.js`, dan `static/js/sampah.js`:
- Semantik inti grant (`issue_grant`, `consume_grant`, validasi HMAC token, TTL 120 detik, penyimpanan memori terisolasi thread) dipertahankan sepenuhnya tanpa perubahan.
- Kriptografi inti (`modules/cryptography/*`) dan `session_keys` tidak disentuh sama sekali.
- Scope baru yang ditambahkan:
  1. `trash.restore` (sekali pakai, TTL 120s): untuk memulihkan item dari Sampah.
  2. `audio.play` (sekali pakai, TTL 120s): untuk memutar audio via stream URL.
  Catatan: `item.delete` sudah terdaftar dalam `SCOPES` pada modul reauth dan berstatus sekali pakai (tidak berada dalam `REUSABLE_TTL`).

#### 1. Daftar Endpoint yang Terkena Perubahan

| Endpoint | Metode | Scope Grant | Sekali Pakai? | Konvensi Resource ID | Keterangan |
|---|---|---|---|---|---|
| `/vault/delete/<int:resource_id>` | `POST` | `item.delete` | Ya (120s) | `resource_id` (int/str) | Pindah ke Sampah untuk dokumen/berkas, media, audio |
| `/secure-notes/delete/<int:resource_id>` | `POST` | `item.delete` | Ya (120s) | `resource_id` (int/str) | Pindah ke Sampah untuk catatan aman |
| `/account-vault/delete/<int:resource_id>` | `POST` | `item.delete` | Ya (120s) | `resource_id` (int/str) | Pindah ke Sampah untuk kredensial akun |
| `/steganography/delete/<int:img_id>` | `POST` | `item.delete` | Ya (120s) | `img_id` (int/str) | Pindah ke Sampah untuk gambar steganografi |
| `/api/sampah/pulihkan` | `POST` | `trash.restore` | Ya (120s) | `None` | Pulihkan item dari Sampah (tunggal maupun banyak sekaligus) |
| `/media-vault/stream/<int:file_id>` | `GET` | `audio.play` | Ya (120s) | `file_id` (int/str) | Mengambil audio untuk diputar di pemutar modal |

#### 2. Urutan Pemeriksaan Keamanan
Mengikuti pola ketat `@require_grant`:
1. Permintaan tanpa grant valid → HTTP 401 Unauthorized (`reason: "missing"` / `"invalid"` / `"expired"`).
2. Permintaan dengan grant yang memiliki scope atau resource_id tidak cocok → HTTP 403 Forbidden (`reason: "scope"` / `"resource"`).
3. Permintaan dengan grant valid tetapi item tidak ditemukan di basis data → HTTP 404 Not Found.
4. Pemeriksaan akses tambahan (misalnya koleksi/album terkunci) tetap dijalankan setelah grant valid.
5. Grant sekali pakai langsung dimusnahkan dari memori server setelah pemakaian pertama; permintaan kedua dengan token yang sama ditolak HTTP 401 (`reason: "invalid"`).

#### 3. Alur Klien
- **Hapus (Soft Delete)**: Seluruh tombol Hapus pada Dokumen, Media, Audio, Catatan, Akun, dan Stego menggunakan atribut `data-reauth="item.delete"` dan `data-reauth-resource="<id>"`. Dialog "yakin hapus?" (`KX.konfirmasiHapus`) dihilangkan untuk soft-delete; klik tombol Hapus langsung membuka dialog verifikasi step-up reauth (`#reauth-modal`). Setelah grant diperoleh, form dikirimkan langsung dan halaman menampilkan notifikasi toast (via flash).
- **Pulihkan**: Tombol Pulihkan di baris tabel maupun tombol Pulihkan Terpilih (massal) meminta verifikasi grant `trash.restore` tanpa dialog konfirmasi tambahan. Mengikuti pola `trash.purge`, permintaan grant dilakukan satu kali untuk aksi (tunggal maupun massal), lalu token grant dikirim via header `X-Reauth-Grant` ke `POST /api/sampah/pulihkan`.
- **Putar Audio**: Mengklik tombol Putar memicu dialog verifikasi grant `audio.play` dengan `resource_id = file_id`. Setelah grant terbit, klien melakukan `fetch('/media-vault/stream/<id>', { headers: { 'X-Reauth-Grant': token } })` satu kali, mengonversi respons ke Blob URL (`URL.createObjectURL(blob)`), memasangnya ke elemen `<audio controls>` di modal, dan membuka modal. Saat modal ditutup, `URL.revokeObjectURL` dipanggil seketika dan atribut `src` audio dilepas sehingga tidak ada cache media yang tertinggal di peramban.

#### 4. Keputusan Tindakan yang Tidak Berubah
Sesuai instruksi butir 4, fitur-fitur berikut tidak mengalami penambahan grant baru:
- Ganti nama berkas/album (`POST /api/collections/...`)
- Pindah folder/album (`POST /api/collections/move`)
- Unggah berkas (`POST /vault/upload`, dsb.)
- Filter pencarian dan pagination
- Buka/edit catatan (tetap memakai `note.open` dan `note.edit`)
- Tampilkan kredensial akun (tetap memakai `account.reveal`)
- Kunci dan lepas kunci berkas/koleksi (tetap memakai `item.unlock` dan `album.unlock`)
- Pratinjau dokumen (tetap memakai `doc.preview`)
- Tampilan media gambar/video (tetap memakai `item.view`)
- Hapus Permanen dan Kosongkan Sampah (tetap menggunakan konfirmasi dialog `KX.konfirmasiHapus` lalu grant `trash.purge`).

#### 5. Tes yang Dihapus atau Diubah pada G2

Sesuai Aturan 6 dan instruksi G2, seluruh penyesuaian tes lama dicatat secara rinci:

1. `tests/test_ub_sampah.py`:
   - `_pindah_ke_sampah`: Diperbarui untuk menerbitkan dan mengirim grant `item.delete` untuk item yang dipindahkan ke sampah via `reauth_grant` dan header `X-Reauth-Grant`.
   - `TestHapusLunak::test_hapus_idempoten_ditolak_saat_sudah_di_sampah`: Ditambahkan grant `item.delete` agar permintaan lolos otentikasi grant dan menguji logika idempotensi (404).
   - `TestHapusLunak::test_sampah_menutup_akses_langsung`: Mengganti pengujian stream dari scope lama `media.stream` ke scope baru `audio.play`.
   - `TestPulihkan`: Seluruh pengujian pemulihan (`test_pulihkan_mengembalikan_item`, `test_pulihkan_respons_json`, `test_pulihkan_tanpa_csrf_ditolak`, `test_pulihkan_gagal_bila_satu_item_tidak_di_sampah`, `test_items_tidak_sah_ditolak`) diperbarui dengan grant `trash.restore` karena endpoint `/api/sampah/pulihkan` kini mewajibkan grant.
   - `TestAntarPengguna::test_pulihkan_milik_orang_lain_ditolak`: Ditambahkan grant `trash.restore` milik pengguna lain.
2. `tests/test_media_routes.py`:
   - `TestMediaStream`: Seluruh pengujian endpoint `/media-vault/stream/{file_id}` diperbarui dari scope lama `media.stream` ke scope baru `audio.play`.
3. `tests/test_j2_grants.py`:
   - `TestMediaStreamGrant`: Diperbarui untuk menguji scope `audio.play` pada `/media-vault/stream/{file_id}`. Tes sifat dapat dipakai berulang tanpa header diubah menjadi tes sifat sekali pakai (`test_audio_play_sekali_pakai_tidak_bisa_dua_kali`) yang memastikan permintaan kedua ditolak 401.
4. `tests/test_encrypted_storage.py`:
   - `TestAccountVaultSesiI::test_hapus_lunak_dengan_grant`, `TestSecureNotesSesiI::test_hapus_lunak_dengan_grant`, `TestVaultSesiI::test_hapus_lunak_dengan_grant`: Diperbarui untuk mengirimkan grant `item.delete`.
5. `tests/test_ub_kunci.py`:
   - Pengujian stream diperbarui menggunakan scope `audio.play` dan pengujian `/vault/delete/` pada `TestSampah` diperbarui dengan grant `item.delete`.
6. `tests/test_u2_kunci_berkas.py`:
   - `test_item_terkunci_di_sampah_tetap_tidak_terjangkau`: Ditambahkan grant `item.delete` pada permintaan hapus berkas.
7. `tests/test_l_idor_blockchain_media.py`:
   - Mengubah scope rute `/media-vault/stream/{id}` menjadi `audio.play` dan `/steganography/delete/{id}` menjadi `item.delete`.

#### 6. Pengujian Kontrak G2 (`tests/test_u2g_kontrak.py`)
- `test_kontrak_ui_tanpa_konfirmasi_dan_dengan_data_reauth`: Memvalidasi bahwa seluruh template dengan tombol Hapus soft-delete (dokumen, media, audio, catatan, akun, stego) memiliki atribut `data-reauth="item.delete"`, dan tidak ada lagi pemanggilan `KX.konfirmasiHapus` untuk soft delete di seluruh skrip JS terkait.
- `test_kontrak_hapus_semua_jenis_dengan_grant_sekali_pakai`: Memeriksa siklus lengkap scope `item.delete` pada seluruh 4 endpoint (file, note, cred, stego): tanpa grant (401), grant scope salah (403), grant sah (302), panggilan kedua (401 invalid), dan urutan grant sebelum 404.
- `test_kontrak_trash_restore_grant_sekali_pakai`: Memeriksa siklus lengkap scope `trash.restore` pada `/api/sampah/pulihkan`: tanpa grant (401), scope salah (403), grant sah (200), panggilan kedua (401 invalid), dan urutan grant sebelum 404.
- `test_kontrak_audio_play_grant_sekali_pakai`: Memeriksa siklus lengkap scope `audio.play` pada `/media-vault/stream/<id>`: tanpa grant (401), scope salah (403), grant sah (200), panggilan kedua (401 invalid), dan urutan grant sebelum 404.

#### 7. Keterbatasan Jujur
1. **Verifikasi per Tindakan pada Aksi Massal**: Untuk pemulihan massal di Sampah, klien menerbitkan satu grant `trash.restore` untuk satu transaksi batch (mengikuti pola `trash.purge`). Namun, untuk soft delete item yang dilakukan secara terpisah di tabel masing-masing, setiap tombol Hapus memicu verifikasi grant per item (`item.delete` dengan `resource_id` item terkait).
2. **Streaming Audio Sekali Pakai & Blob URL**: Karena grant `audio.play` bersifat sekali pakai, pemutaran audio di peramban tidak dapat menggunakan URL stream langsung di `<audio src>` (karena browser dapat mengirimkan beberapa permintaan HTTP Range terpisah yang akan menggagalkan grant sekali pakai). Solusinya, audio diunduh via fetch tunggal dengan header `X-Reauth-Grant`, dijadikan Blob URL di memori, dan dimusnahkan seketika saat modal ditutup.

#### 8. Riwayat Commit G2

| Commit | Pesan Commit | Deskripsi |
|---|---|---|
| (commit 1) | `[U2g] verifikasi hapus dan pulihkan` | Grant item.delete pada vault/notes/account/stego delete, grant trash.restore pada pulihkan sampah, pembaruan template & JS tanpa konfirmasi hapus |
| (commit 2) | `[U2g] verifikasi putar audio` | Scope audio.play sekali pakai pada media-vault/stream, fetch blob URL sekali di sisi klien dan pelepasan saat modal tutup |
| (commit 3) | `[U2g] tes dan dokumen g2` | Pembaruan tes yang disesuaikan, uji kontrak baru test_u2g_kontrak.py, dokumen U2g.md bagian G2 |



