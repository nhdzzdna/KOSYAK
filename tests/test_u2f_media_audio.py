"""
tests/test_u2f_media_audio.py
─────────────────────────────
Uji kontrak perbaikan F1 (Media dan Audio):
- Bagian "Semua" pada Media hanya memuat item yang tidak berada di album.
- Tidak ada lagi bagian atau chip "Tanpa album" pada Media dan Audio.
- Form ganti nama album dan ganti nama berkas penampil ada dan tersembunyi
  saat awal.
- Ganti nama folder Dokumen memakai endpoint rename yang sama.
- Halaman Audio menjadi daftar satu tingkat tanpa UI folder.
"""

import io
import os
import pytest
import config
from app import create_app
from database.db import get_db, init_db
from modules.authentication import reauth
from modules.cryptography import session_keys
from modules.cryptography.key_management import purpose_key
from modules.cryptography.database_encryption import encrypt_field, field_aad
from modules.cryptography.file_encryption import encrypt_stream, file_aad, generate_stored_name

DEK = bytes(range(32))
ISI_AUDIO = b"ID3\x03\x00\x00\x00\x00\x00#TSSE\x00\x00\x00\x0f\x00\x00\x01\xff\xfeL\x00a\x00v\x00f\x005\x008\x00"
ISI_GAMBAR = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"


@pytest.fixture()
def app(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DATABASE_PATH", str(tmp_path / "u2f.db"))
    monkeypatch.setattr(config, "ENCRYPTED_FILES_DIR", str(tmp_path / "enc"))
    monkeypatch.setattr(config, "STEGO_IMAGES_DIR", str(tmp_path / "stego"))
    monkeypatch.setattr(config, "TEMPORARY_FILES_DIR", str(tmp_path / "tmp"))
    monkeypatch.setattr(config, "WINAMP_PATH", str(tmp_path / "winamp-simulasi.exe"))
    init_db()
    with get_db() as db:
        db.execute(
            """INSERT OR IGNORE INTO users
               (id, username, email, password_hash, salt) VALUES (?,?,?,?,?)""",
            (1, "u2fuser", "u2fuser@contoh.test", "hash", "garam"),
        )
        db.commit()
    application = create_app()
    application.config["TESTING"] = True
    reauth.clear()
    return application


@pytest.fixture()
def client(app):
    c = app.test_client()
    with c.session_transaction() as sess:
        sess["user_id"] = 1
        sess["username"] = "u2fuser"
        sid = session_keys.create_session_id()
        sess["session_id"] = sid
        session_keys.put(sid, DEK)
    return c


def _file_id(nama: str, file_type: str) -> int:
    db_key = purpose_key(DEK, "database")
    fkey = purpose_key(DEK, "file")
    stored = generate_stored_name()
    isi = ISI_AUDIO if file_type == "audio" else ISI_GAMBAR
    enc_res = encrypt_stream(
        io.BytesIO(isi),
        os.path.join(config.ENCRYPTED_FILES_DIR, stored),
        fkey,
        file_aad(1, stored),
    )
    token = encrypt_field(nama, db_key, field_aad(1, "vault_files", "original_name"))
    with get_db() as db:
        cur = db.execute(
            """INSERT INTO vault_files
               (user_id, original_name, stored_name, file_type, file_size,
                sha256_hash, sha256_ciphertext)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (1, token, stored, file_type, len(isi),
             enc_res["sha256_plaintext"], enc_res["sha256_ciphertext"]),
        )
        db.commit()
        return cur.lastrowid


def _album(nama: str, kind: str, file_id: int) -> int:
    db_key = purpose_key(DEK, "database")
    token = encrypt_field(nama, db_key, field_aad(1, "collections", "name_enc"))
    with get_db() as db:
        cur = db.execute(
            "INSERT INTO collections (user_id, name_enc, kind, locked) VALUES (?,?,?,0)",
            (1, token, kind),
        )
        cid = cur.lastrowid
        db.execute(
            "INSERT INTO collection_items (collection_id, file_id, state) VALUES (?,?,?)",
            (cid, file_id, "normal"),
        )
        db.commit()
        return cid


def test_media_semua_hanya_di_luar_album(client):
    _file_id("media_di_luar.png", "image")
    fid_album = _file_id("media_di_album.png", "image")
    _album("Album Uji", "album", fid_album)

    html = client.get("/media-vault").get_data(as_text=True)
    assert 'id="collection-all-section"' in html
    assert 'id="collection-unfiled-section"' not in html
    assert "media_di_luar.png" in html
    assert "media_di_album.png" not in html
    assert 'id="media-gallery-title"' not in html


def test_media_form_ganti_nama_tersembunyi_saat_awal(client):
    html = client.get("/media-vault").get_data(as_text=True)

    assert 'id="album-rename"' in html
    assert 'id="album-rename-input"' in html
    assert 'id="album-rename-form"' in html
    assert 'id="viewer-rename"' in html
    assert 'id="viewer-rename-input"' in html
    assert 'id="viewer-rename-form"' in html
    assert html.count('id="album-rename-form" class="kx-doc-folder-rename-form media-rename-form" hidden') == 1
    assert html.count('id="viewer-rename-form" class="kx-media-rename-form" hidden') == 1


def test_media_js_memanggil_endpoint_rename():
    with open("static/js/media_albums.js", "r", encoding="utf-8") as f:
        js = f.read()

    assert "/rename" in js
    assert "album-rename" in js
    assert "viewer-rename" in js
    assert "perbaruiNamaAlbum" in js
    assert "window.KX.toast" in js
    assert "unfiled-grid" not in js


def test_dokumen_form_ganti_nama_folder_tersembunyi_saat_awal():
    with open("templates/vault.html", "r", encoding="utf-8") as f:
        html = f.read()
    with open("static/js/collection_folders.js", "r", encoding="utf-8") as f:
        js = f.read()

    assert 'id="folder-rename"' in html
    assert 'id="folder-rename-input"' in html
    assert 'id="folder-rename-form"' in html
    assert 'id="folder-rename-form" class="kx-doc-folder-rename-form doc-folder-rename" hidden' in html
    assert "/rename" in js
    assert "formGantiNama.addEventListener('submit'" in js


def test_audio_tanpa_ui_folder(client):
    fid = _file_id("trek_biasa.mp3", "audio")
    assert fid
    html = client.get("/audio").get_data(as_text=True)

    assert 'id="collection-all-section"' in html
    assert 'id="collection-unfiled-section"' not in html
    assert 'id="collection-page"' not in html
    for terlarang in ("folder-create-form", "folder-detail", "data-folder-open",
                      "move-target", "move-button", "audio-unfiled-empty",
                      "data-folder-badge"):
        assert terlarang not in html
    assert "collection_folders.js" not in html
    assert 'id="audio-search"' in html
    assert 'id="music-audio"' in html
    assert 'id="selection-bar"' in html
    assert "data-track-lock" in html
    assert "data-track-unlock" not in html


def test_audio_trek_terkunci_tampil_dan_bisa_dilepas(client):
    fid = _file_id("trek_kunci.mp3", "audio")
    with get_db() as db:
        db.execute("UPDATE vault_files SET locked=1 WHERE id=?", (fid,))
        db.commit()

    html = client.get("/audio").get_data(as_text=True)
    assert "trek_kunci.mp3" in html
    assert 'data-locked="1"' in html
    assert "data-track-unlock" in html
    assert "Terkunci" in html


def test_audio_css_tanpa_kelas_folder():
    with open("static/css/halaman/audio.css", "r", encoding="utf-8") as f:
        css = f.read()
    assert ".kx-audio-folder" not in css
