"""
tests/test_perbaikan_viewer_pratinjau.py
────────────────────────────────────────
Uji regresi penampil media, menu titik tiga, dan pratinjau dokumen:
- penampil media tidak mengandalkan inline display:none;
- dropdown kartu media hanya memuat aksi Unduh/Hapus (satu tombol Lihat utama);
- CSP mengizinkan blob: untuk img-src dan frame-src, serta object-src 'none';
- tombol Pratinjau disembunyikan untuk DOC/DOCX/XLS/XLSX/PPT/PPTX;
- modal pratinjau dibuka/ditutup lewat KX.modal tanpa inline display.
"""

import io
import os
import re
from pathlib import Path

import pytest
from PIL import Image

import config
from app import create_app
from database.db import get_db, init_db
from modules.authentication import reauth
from modules.cryptography import session_keys
from modules.cryptography.database_encryption import encrypt_field, field_aad
from modules.cryptography.file_encryption import (
    encrypt_stream, file_aad, generate_stored_name,
)
from modules.cryptography.key_management import purpose_key

DEK = bytes(range(32))
ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture()
def app(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DATABASE_PATH", str(tmp_path / "viewer-pratinjau.db"))
    monkeypatch.setattr(config, "ENCRYPTED_FILES_DIR", str(tmp_path / "enc"))
    monkeypatch.setattr(config, "STEGO_IMAGES_DIR", str(tmp_path / "stego"))
    monkeypatch.setattr(config, "TEMPORARY_FILES_DIR", str(tmp_path / "tmp"))
    monkeypatch.setattr(config, "WINAMP_PATH", str(tmp_path / "winamp-tiada.exe"))
    os.makedirs(config.ENCRYPTED_FILES_DIR, exist_ok=True)
    init_db()
    with get_db() as db:
        db.execute(
            """INSERT OR IGNORE INTO users
               (id, username, email, password_hash, salt) VALUES (?,?,?,?,?)""",
            (1, "pemilikuji", "pemilikuji@contoh.test", "hash", "garam"),
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
        sess["username"] = "pemilikuji"
        sid = session_keys.create_session_id()
        sess["session_id"] = sid
        session_keys.put(sid, DEK)
    return c


def _unggah(nama: str, jenis: str = "document") -> int:
    if jenis == "image":
        penyangga = io.BytesIO()
        Image.new("RGB", (20, 20), (30, 120, 200)).save(penyangga, format="PNG")
        data = penyangga.getvalue()
    else:
        data = b"Isi dokumen uji pratinjau.\n"

    stored = generate_stored_name()
    hasil = encrypt_stream(
        io.BytesIO(data),
        os.path.join(config.ENCRYPTED_FILES_DIR, stored),
        purpose_key(DEK, "file"),
        file_aad(1, stored),
    )
    nama_terenkripsi = encrypt_field(
        nama, purpose_key(DEK, "database"),
        field_aad(1, "vault_files", "original_name"),
    )
    with get_db() as db:
        kursor = db.execute(
            """INSERT INTO vault_files
               (user_id, original_name, stored_name, file_type, file_size,
                sha256_hash, sha256_ciphertext)
               VALUES (?,?,?,?,?,?,?)""",
            (1, nama_terenkripsi, stored, jenis, len(data),
             hasil["sha256_plaintext"], hasil["sha256_ciphertext"]),
        )
        db.commit()
        return kursor.lastrowid


def _baris_dokumen(html: str, nama: str) -> str:
    penanda = 'data-name="' + nama + '"'
    awal_nama = html.find(penanda)
    assert awal_nama != -1, f"baris {nama} tidak ditemukan"
    penanda_baris = '<div class="kx-doc-row collection-item doc-file-row"'
    awal = html.rfind(penanda_baris, 0, awal_nama)
    akhir = html.find(penanda_baris, awal_nama)
    return html[awal: akhir if akhir != -1 else len(html)]


def test_csp_mengizinkan_blob_pratinjau(client):
    csp = client.get("/documents").headers.get("Content-Security-Policy", "")
    assert "img-src 'self' data: blob:" in csp
    assert "frame-src 'self' blob:" in csp
    assert "object-src 'none'" in csp


def test_media_viewer_tidak_mengandalkan_inline_display(client):
    _unggah("pemandangan.png", "image")
    html = client.get("/media-vault").get_data(as_text=True)
    tag = re.search(r'<div id="media-viewer"[^>]*>', html)
    assert tag
    assert "display" not in tag.group(0)

    css = (ROOT / "static" / "css" / "components.css").read_text(encoding="utf-8")
    assert re.search(r"\.kx-modal-overlay\s*\{[^}]*display:\s*none", css)
    assert re.search(r"\.kx-modal-overlay\.is-open\s*\{\s*display:\s*flex", css)

    js = (ROOT / "static" / "js" / "media_albums.js").read_text(encoding="utf-8")
    assert "penampil.style.display" not in js
    assert "CryptixLock.pilih(kartu, bukaPenampil, 'item.view')" in js


def test_dropdown_media_tanpa_item_lihat(client):
    _unggah("foto_satu.png", "image")
    _unggah("foto_dua.jpg", "image")
    html = client.get("/media-vault").get_data(as_text=True)

    dropdown = re.findall(
        r'<div class="kx-media-menu-dropdown"[^>]*>(.*?)</div>', html, re.DOTALL
    )
    # Tiap berkas tampil di "Semua" dan "Tanpa album".
    assert len(dropdown) == 4
    for isi in dropdown:
        assert "Lihat" not in isi
        assert "data-open-media" not in isi
        assert "Unduh" in isi
        assert "Hapus" in isi

    # Satu tombol Lihat utama plus satu thumbnail pembuka per kartu.
    assert html.count("data-open-media") == 8


def test_pratinjau_disembunyikan_untuk_format_office(client):
    untuk_disembunyikan = [
        "draft.doc", "draft.docx", "tabel.xls", "tabel.xlsx",
        "slide.ppt", "slide.pptx",
    ]
    for nama in untuk_disembunyikan + ["aman.pdf", "catatan.txt"]:
        _unggah(nama)

    html = client.get("/documents").get_data(as_text=True)
    for nama in untuk_disembunyikan:
        baris = _baris_dokumen(html, nama)
        assert 'data-reauth="doc.preview"' not in baris, nama
        assert 'data-reauth="file.download"' in baris, nama
    for nama in ("aman.pdf", "catatan.txt"):
        assert 'data-reauth="doc.preview"' in _baris_dokumen(html, nama)

    js = (ROOT / "static" / "js" / "collection_folders.js").read_text(encoding="utf-8")
    for ekstensi in (".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx"):
        assert "'" + ekstensi + "'" in js


def test_modal_pratinjau_memakai_kx_modal_tanpa_inline_display(client):
    html = client.get("/documents").get_data(as_text=True)
    tag = re.search(r'<div id="preview-modal"[^>]*>', html)
    assert tag
    assert "display" not in tag.group(0)

    js = (ROOT / "static" / "js" / "dokumen.js").read_text(encoding="utf-8")
    assert "KX.modal.buka(modal)" in js
    assert "KX.modal.tutup(modal)" in js
    assert "modal.style.display" not in js
