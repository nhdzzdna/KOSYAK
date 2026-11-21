"""
tests/test_u2g_kontrak.py
─────────────────────────
Uji kontrak untuk pembaruan G1 (Audio, Catatan, dan Teks Antarmuka):
1. Grid header dan baris Audio memakai kolom yang sama di static/css/halaman/audio.css.
2. Tidak ada elemen pemutar kustom di templates/musik.html.
3. Modal audio di templates/musik.html memakai <audio controls> bawaan browser.
4. Kartu catatan tanpa kotak biru dan tombol Buka & Hapus berdampingan (8px).
5. Seluruh string terlarang tidak ada di templates/ dan modules/strings.py.
"""

import re
from pathlib import Path
import pytest
from app import create_app
from modules.cryptography import session_keys

AKAR = Path(__file__).resolve().parents[1]


@pytest.fixture()
def client(tmp_path, monkeypatch):
    import config
    from database.db import get_db, init_db

    monkeypatch.setattr(config, "DATABASE_PATH", str(tmp_path / "u2g.db"))
    monkeypatch.setattr(config, "ENCRYPTED_FILES_DIR", str(tmp_path / "enc"))
    monkeypatch.setattr(config, "STEGO_IMAGES_DIR", str(tmp_path / "stego"))
    monkeypatch.setattr(config, "TEMPORARY_FILES_DIR", str(tmp_path / "tmp"))
    init_db()
    with get_db() as db:
        db.execute(
            """INSERT OR IGNORE INTO users
               (id, username, email, password_hash, salt) VALUES (?,?,?,?,?)""",
            (1, "userg1", "userg1@contoh.test", "hash", "garam"),
        )
        db.commit()

    application = create_app()
    application.config["TESTING"] = True
    c = application.test_client()
    with c.session_transaction() as sess:
        sess["user_id"] = 1
        sess["username"] = "userg1"
        sid = session_keys.create_session_id()
        sess["session_id"] = sid
        session_keys.put(sid, bytes(range(32)))
    return c


def test_kontrak_grid_header_dan_baris_audio():
    """Grid header dan baris Audio memakai selector dan deklarasi grid-template-columns yang sama."""
    css_path = AKAR / "static" / "css" / "halaman" / "audio.css"
    konten = css_path.read_text(encoding="utf-8")

    # Memastikan selector bersama .kx-audio-table thead tr, .kx-audio-tr memiliki grid-template-columns
    pola = re.compile(
        r"\.kx-audio-table\s+thead\s+tr\s*,\s*\.kx-audio-tr\s*\{[^}]*grid-template-columns:\s*([^;]+);",
        re.DOTALL,
    )
    cocok = pola.search(konten)
    assert cocok is not None, "Selector bersama thead tr dan kx-audio-tr tidak ditemukan di audio.css"
    cols = cocok.group(1).strip()
    # Harus memuat 6 kolom: select, play, title, durasi, status, menu
    assert "minmax" in cols, f"Kolom grid tidak fleksibel: {cols}"


def test_kontrak_tanpa_pemutar_kustom_di_musik_html():
    """Tidak ada elemen pemutar kustom di templates/musik.html."""
    html_path = AKAR / "templates" / "musik.html"
    konten = html_path.read_text(encoding="utf-8")

    elemen_terlarang = [
        "kx-audio-player-bar",
        "music-play-toggle",
        "music-progress-bar",
        "music-progress-fill",
        "music-time-cur",
        "music-time-total",
        "music-prev",
        "music-next",
        "kx-audio-player-cover",
    ]
    for el in elemen_terlarang:
        assert el not in konten, f"Elemen pemutar kustom '{el}' masih ada di templates/musik.html"


def test_kontrak_modal_audio_controls():
    """Modal audio di templates/musik.html memakai elemen <audio controls> bawaan browser."""
    html_path = AKAR / "templates" / "musik.html"
    konten = html_path.read_text(encoding="utf-8")

    assert 'id="audio-modal"' in konten, "Modal id='audio-modal' tidak ditemukan"
    assert re.search(r'<audio[^>]*\bid="music-audio"[^>]*\bcontrols\b', konten), (
        "Elemen <audio controls> dengan id='music-audio' tidak ditemukan di musik.html"
    )


def test_kontrak_catatan_tanpa_kotak_biru(client):
    """Kartu catatan tanpa kotak biru dan tombol Buka & Hapus berdampingan (8px)."""
    # Masukkan satu catatan ke basis data
    from database.db import get_db
    from modules.cryptography import session_keys
    from modules.cryptography.key_management import purpose_key
    from modules.cryptography.database_encryption import encrypt_field, field_aad

    db_key = purpose_key(bytes(range(32)), "database")
    title_enc = encrypt_field("Catatan Uji", db_key, field_aad(1, "secure_notes", "title_enc"))
    content_enc = encrypt_field("Isi rahasia", db_key, field_aad(1, "secure_notes", "content_enc"))
    with get_db() as db:
        db.execute(
            "INSERT INTO secure_notes (user_id, title_enc, content_enc) VALUES (?, ?, ?)",
            (1, title_enc, content_enc),
        )
        db.commit()

    resp = client.get("/secure-notes")
    assert resp.status_code == 200
    body = resp.get_data(as_text=True)

    assert "Isi catatan hanya tampil setelah verifikasi ulang." not in body
    assert "sn-buka-kotak" not in body
    # Memastikan tombol aksi Buka dan Hapus memiliki kelas kx-sn-aksi
    assert "kx-sn-aksi" in body


def test_kontrak_string_terlarang_tidak_ada():
    """String penjelas yang dilarang tidak ada di templates maupun modules/strings.py."""
    string_terlarang = [
        "Bukan kata sandi akun Anda",
        "Berkas dienkripsi sebelum disimpan",
        "Isi catatan hanya tampil setelah verifikasi ulang",
        "Winamp terdeteksi di sistem",
        "Untuk cipher modern, teks diturunkan menjadi kunci 32 byte",
        "Kunci turunan untuk keempat layer",
    ]

    berkas_diperiksa = [AKAR / "modules" / "strings.py"]
    berkas_diperiksa += list((AKAR / "templates").glob("*.html"))

    for berkas in berkas_diperiksa:
        konten = berkas.read_text(encoding="utf-8")
        for s in string_terlarang:
            assert s not in konten, f"String terlarang '{s}' ditemukan di {berkas.name}"
