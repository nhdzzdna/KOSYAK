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
