"""
tests/test_crypto_routes.py
───────────────────────────
Uji rute Crypto Tools: form ber-CSRF, kunci teks ChaCha20/Blowfish,
tabel jejak untuk semua cipher dan aksi, tahapan Super Encryption, serta
ketiadaan hasil maupun kunci turunan di cookie/HTML.
"""

import base64
import html
import re
from pathlib import Path

import pytest

import config
from app import create_app
from database.db import get_db, init_db
from modules.cryptography import session_keys
from modules.cryptography.classical_cipher_1 import vigenere_letter_encrypt
from modules.cryptography.classical_cipher_2 import playfair_encrypt
from modules.cryptography.modern_cipher_1 import chacha20_encrypt
from modules.cryptography.modern_cipher_2 import blowfish_encrypt
from modules.cryptography.super_encryption import super_encrypt
from routes.crypto_routes import _tool_key

PASSPHRASE = "passphrase-rute-uji-42"


@pytest.fixture()
def app(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DATABASE_PATH", str(tmp_path / "crypto_uji.db"))
    monkeypatch.setattr(config, "ENCRYPTED_FILES_DIR", str(tmp_path / "encrypted"))
    monkeypatch.setattr(config, "STEGO_IMAGES_DIR", str(tmp_path / "stego"))
    monkeypatch.setattr(config, "TEMPORARY_FILES_DIR", str(tmp_path / "temporary"))
    init_db()
    with get_db() as db:
        db.execute(
            """INSERT INTO users
               (id, username, email, password_hash, salt) VALUES (?,?,?,?,?)""",
            (1, "pengujian", "pengujian@contoh.test", "hash", "garam"),
        )
        db.commit()

    application = create_app()
    application.config["TESTING"] = True
    return application


@pytest.fixture()
def client(app):
    c = app.test_client()
    with c.session_transaction() as sess:
        sess["user_id"] = 1
        sess["username"] = "pengujian"
        sid = session_keys.create_session_id()
        sess["session_id"] = sid
        session_keys.put(sid, b"\x5a" * 32)
    return c


def _csrf_token(client) -> str:
    page = client.get("/crypto-tools")
    assert page.status_code == 200
    match = re.search(r'name="csrf_token" value="([^"]+)"', page.get_data(as_text=True))
    assert match, "token CSRF tidak ditemukan pada form"
    return match.group(1)


def _post(client, **fields):
    fields.setdefault("csrf_token", _csrf_token(client))
    return client.post("/crypto-tools", data=fields)


def _first_output(html_text: str):
    match = re.search(r'<pre class="kx-code[^"]*"[^>]*>(.*?)</pre>', html_text, re.S)
    return html.unescape(match.group(1)) if match else None


def _trace_tables(html_text: str) -> list[str]:
    return re.findall(
        r'<table class="kx-table kx-ct-trace">(.*?)</table>', html_text, re.S
    )


def _teks_sel(sel: str, strip: bool = True) -> str:
    teks = html.unescape(re.sub(r"<[^>]+>", "", sel))
    return teks.strip() if strip else teks


def _header_tabel(tabel: str) -> list[str]:
    thead = re.search(r"<thead>(.*?)</thead>", tabel, re.S)
    assert thead, "header tabel jejak tidak ditemukan"
    return [
        _teks_sel(sel)
        for sel in re.findall(r"<th[^>]*>(.*?)</th>", thead.group(1), re.S)
    ]


def _baris_tabel(tabel: str) -> list[list[str]]:
    baris: list[list[str]] = []
    for row in re.findall(r"<tr>(.*?)</tr>", tabel, re.S)[1:]:
        sel = re.findall(r"<td[^>]*>(.*?)</td>", row, re.S)
        if sel:
            baris.append([_teks_sel(item, strip=False) for item in sel])
    return baris


class TestCryptoToolsForm:
    def test_form_contains_csrf_and_stages_option(self, client):
        page = client.get("/crypto-tools")
        body = page.get_data(as_text=True)
        assert page.status_code == 200
        assert 'name="csrf_token"' in body
        assert 'name="show_stages"' in body
        assert 'id="ct-show-stages"' in body
        assert "Tampilkan tahapan" in body
        assert 'autocomplete="off"' in body
        assert 'autocomplete="new-password"' not in body
        assert 'data-lpignore="true"' in body
        assert "Kunci enkripsi" in body
        assert "Bukan kata sandi akun Anda." not in body
        assert "data-kx-sandi" not in body

    def test_kunci_dan_passphrase_tidak_diisi_otomatis(self, client):
        body = client.get("/crypto-tools").get_data(as_text=True)
        form = re.search(r'<form[^>]*id="crypto-form"[^>]*>', body)
        assert form and 'autocomplete="off"' in form.group(0)

        kunci = re.search(r'<input[^>]*id="ct-kunci"[^>]*>', body)
        assert kunci
        for atribut in ('autocomplete="off"', 'data-lpignore="true"',
                        'data-1p-ignore', 'data-bwignore',
                        'data-form-type="other"', 'readonly'):
            assert atribut in kunci.group(0)

        passphrase = re.search(r'<input[^>]*id="ct-passphrase"[^>]*>', body)
        assert passphrase
        assert 'type="text"' in passphrase.group(0)
        assert 'name="passphrase"' in passphrase.group(0)
        assert 'class="kx-input kx-ct-kunci"' in passphrase.group(0)
        for atribut in ('autocomplete="off"', 'data-lpignore="true"',
                        'data-1p-ignore', 'data-bwignore',
                        'data-form-type="other"', 'readonly'):
            assert atribut in passphrase.group(0)

        js = (Path(__file__).resolve().parents[1] /
              "static" / "js" / "crypto_tools.js").read_text(encoding="utf-8")
        assert "function kosongkanKunci" in js
        assert "addEventListener('load', kosongkanKunci)" in js
        assert "addEventListener('pageshow', kosongkanKunci)" in js

    def test_hint_vigenere_dan_pbkdf2_tersembunyi_bawaan(self, client):
        body = client.get("/crypto-tools").get_data(as_text=True)
        assert re.search(r'data-hint-vigenere[^>]*\bhidden\b', body)
        assert 'data-hint-kunci' not in body
        assert re.search(r'id="ct-passphrase-field"[^>]*\bhidden\b', body)

    def test_post_without_csrf_rejected(self, client):
        page = client.post("/crypto-tools", data={
            "cipher": "super", "action": "encrypt",
            "text": "uji", "passphrase": PASSPHRASE,
        })
        assert page.status_code == 400


class TestSuperEncryptionRoute:
    def test_encrypt_shows_each_layer(self, client):
        page = _post(
            client, cipher="super", action="encrypt",
            text="Halo Super Encryption", passphrase=PASSPHRASE,
            show_stages="1",
        )
        body = page.get_data(as_text=True)
        assert page.status_code == 200
        assert "CXSE2." in body
        for label in (
            "Layer 1 — Vigenere", "Layer 2 — Playfair",
            "Layer 3 — ChaCha20", "Layer 4 — Blowfish-CBC",
        ):
            assert label in body

    def test_encrypt_without_checkbox_has_no_stages(self, client):
        page = _post(
            client, cipher="super", action="encrypt",
            text="Halo", passphrase=PASSPHRASE,
        )
        body = page.get_data(as_text=True)
        assert "CXSE2." in body
        assert "kx-ct-tahapan" not in body
        assert len(_trace_tables(body)) == 0

    def test_decrypt_roundtrip(self, client):
        pesan = "Pesan terenkripsi lewat rute"
        enc = _post(
            client, cipher="super", action="encrypt",
            text=pesan, passphrase=PASSPHRASE,
        )
        ciphertext = _first_output(enc.get_data(as_text=True))
        assert ciphertext and ciphertext.startswith("CXSE2.")
        dec = _post(
            client, cipher="super", action="decrypt",
            text=ciphertext, passphrase=PASSPHRASE,
        )
        assert pesan in dec.get_data(as_text=True)

    def test_wrong_passphrase_shows_error(self, client):
        enc = _post(
            client, cipher="super", action="encrypt",
            text="rahasia", passphrase=PASSPHRASE,
        )
        ciphertext = _first_output(enc.get_data(as_text=True))
        dec = _post(
            client, cipher="super", action="decrypt",
            text=ciphertext, passphrase="salah",
        )
        body = dec.get_data(as_text=True)
        assert "CXSE2." not in (_first_output(body) or "")
        assert "kx-infobox-danger" in body
        assert not _trace_tables(body)

    def test_output_not_written_to_cookie(self, client):
        enc = _post(
            client, cipher="super", action="encrypt",
            text="larangan-ke-cookie", passphrase=PASSPHRASE,
        )
        ciphertext = _first_output(enc.get_data(as_text=True))
        assert ciphertext
        for header in enc.headers.getlist("Set-Cookie"):
            assert ciphertext not in header
            assert "larangan-ke-cookie" not in header


class TestIndividualCipherRoute:
    def test_chacha20_with_text_key_encrypts(self, client):
        """Kunci berupa teks tidak lagi membuat bytes.fromhex gagal."""
        page = _post(
            client, cipher="chacha20", action="encrypt",
            text="pesan chacha", key="kunci teks biasa",
        )
        body = page.get_data(as_text=True)
        assert page.status_code == 200
        assert "kx-infobox-danger" not in body
        token = _first_output(body)
        assert token and ":" in token

    def test_chacha20_text_key_roundtrip(self, client):
        enc = _post(
            client, cipher="chacha20", action="encrypt",
            text="putar balik chacha", key="kunci teks biasa",
        )
        token = _first_output(enc.get_data(as_text=True))
        dec = _post(
            client, cipher="chacha20", action="decrypt",
            text=token, key="kunci teks biasa",
        )
        assert "putar balik chacha" in dec.get_data(as_text=True)

    def test_blowfish_text_key_roundtrip(self, client):
        """Kunci Blowfish diturunkan dengan PBKDF2 bersalt, bukan SHA-256 polos."""
        enc = _post(
            client, cipher="blowfish", action="encrypt",
            text="putar balik blowfish", key="rahasia-123",
        )
        body = enc.get_data(as_text=True)
        assert "kx-infobox-danger" not in body
        token = _first_output(body)
        assert token and ":" in token
        dec = _post(
            client, cipher="blowfish", action="decrypt",
            text=token, key="rahasia-123",
        )
        assert "putar balik blowfish" in dec.get_data(as_text=True)

    def test_blowfish_wrong_key_shows_error(self, client):
        enc = _post(
            client, cipher="blowfish", action="encrypt",
            text="rahasia", key="kunci-satu",
        )
        token = _first_output(enc.get_data(as_text=True))
        dec = _post(
            client, cipher="blowfish", action="decrypt",
            text=token, key="kunci-dua",
        )
        assert "kx-infobox-danger" in dec.get_data(as_text=True)

    def test_empty_key_shows_error(self, client):
        page = _post(
            client, cipher="chacha20", action="encrypt",
            text="pesan", key="",
        )
        assert "kx-infobox-danger" in page.get_data(as_text=True)


class TestSuperEncryptionTraceRoute:
    def test_encrypt_trace_tables_and_limits(self, client):
        page = _post(
            client, cipher="super", action="encrypt",
            text="A" * 300, passphrase=PASSPHRASE,
            show_stages="1",
        )
        body = page.get_data(as_text=True)
        assert page.status_code == 200
        assert len(_trace_tables(body)) == 4
        assert "Pasangan Asal" in body
        assert "Sebelum (hex)" in body
        assert "ditampilkan 200 pertama" in body
        assert "ditampilkan 100 pasangan pertama" in body
        assert "ditampilkan 64 byte pertama" in body
        assert PASSPHRASE not in body

    def test_encrypt_masks_vigenere_key(self, client):
        page = _post(
            client, cipher="super", action="encrypt",
            text="Halo Dunia", passphrase=PASSPHRASE,
            show_stages="1",
        )
        body = page.get_data(as_text=True)
        assert "***" in body
        assert PASSPHRASE not in body


@pytest.mark.parametrize("cipher, aksi, kunci", [
    ("vigenere", "encrypt", "KUNCI"),
    ("vigenere", "decrypt", "KUNCI"),
    ("playfair", "encrypt", "KUNCIUTAMA"),
    ("playfair", "decrypt", "KUNCIUTAMA"),
    ("chacha20", "encrypt", "kunci-teks-42"),
    ("chacha20", "decrypt", "kunci-teks-42"),
    ("blowfish", "encrypt", "kunci-teks-42"),
    ("blowfish", "decrypt", "kunci-teks-42"),
])
def test_tabel_jejak_tunggal_tiap_cipher_dan_aksi(client, cipher, aksi, kunci):
    """Delapan kombinasi cipher x aksi memuat satu tabel jejak yang benar."""
    pesan = "TEKSRAHASIA" if cipher == "playfair" else "Halo Jejak 42"
    enkripsi = aksi == "encrypt"
    if cipher == "vigenere":
        masukan = pesan if enkripsi else vigenere_letter_encrypt(pesan, kunci)
    elif cipher == "playfair":
        masukan = pesan if enkripsi else playfair_encrypt(pesan, kunci)
    else:
        bkey = _tool_key(kunci)
        if cipher == "chacha20":
            masukan = pesan if enkripsi else chacha20_encrypt(pesan, bkey)
        else:
            masukan = pesan if enkripsi else blowfish_encrypt(pesan, bkey)

    page = _post(
        client, cipher=cipher, action=aksi, text=masukan, key=kunci, show_stages="1",
    )
    body = page.get_data(as_text=True)
    assert page.status_code == 200
    assert "kx-infobox-danger" not in body
    assert "kx-ct-tahapan" in body

    tabel = _trace_tables(body)
    assert len(tabel) == 1, "setiap alat tunggal hanya menghasilkan satu tabel jejak"
    if cipher == "vigenere":
        assert _header_tabel(tabel[0]) == ["Posisi", "Asal", "Kunci", "Hasil"]
        batas = 200
    elif cipher == "playfair":
        assert _header_tabel(tabel[0]) == [
            "Pasangan Asal", "Pasangan Hasil", "Aturan",
        ]
        batas = 100
    else:
        assert _header_tabel(tabel[0]) == [
            "Offset", "Sebelum (hex)", "Sesudah (hex)",
        ]
        batas = 64

    baris = _baris_tabel(tabel[0])
    assert baris
    assert len(baris) <= batas

    # Kunci turunan (_tool_key) dan kunci yang diketik tidak boleh bocor.
    if cipher in ("chacha20", "blowfish"):
        assert kunci not in body
        assert _tool_key(kunci).hex() not in body
    else:
        assert kunci not in body

    hasil = _first_output(body)
    if cipher == "vigenere":
        assert "".join(b[3] for b in baris) == (hasil if enkripsi else pesan)
        assert all(b[2] for b in baris if b[1].isalpha())
    elif cipher == "playfair":
        assert "".join(b[1] for b in baris) == (hasil if enkripsi else pesan)
        assert all(b[2] in ("baris sama", "kolom sama", "persegi") for b in baris)
    elif enkripsi:
        assert bytes.fromhex("".join(b[2] for b in baris)) == base64.b64decode(
            hasil.split(":", 1)[1]
        )
    else:
        # Byte padding Blowfish tidak punya pasangan plaintext; sel itu memakai em dash.
        heksa = "".join(b[2] for b in baris if b[2] and b[2] != "—")
        assert bytes.fromhex(heksa).decode("utf-8") == pesan


@pytest.mark.parametrize("aksi", ["encrypt", "decrypt"])
def test_jejak_super_enkripsi_dan_dekripsi(client, aksi):
    """Super menampilkan empat jejak; dekripsi memakai urutan layer terbalik."""
    pesan = "Halo Jejak Super"
    enkripsi = aksi == "encrypt"
    masukan = pesan if enkripsi else super_encrypt(pesan, passphrase=PASSPHRASE)
    page = _post(
        client, cipher="super", action=aksi, text=masukan, passphrase=PASSPHRASE, show_stages="1",
    )
    body = page.get_data(as_text=True)
    assert page.status_code == 200
    assert "kx-infobox-danger" not in body
    assert PASSPHRASE not in body

    urutan = (
        ["Layer 1 — Vigenere", "Layer 2 — Playfair",
         "Layer 3 — ChaCha20", "Layer 4 — Blowfish-CBC"]
        if enkripsi else
        ["Layer 4 — Blowfish-CBC", "Layer 3 — ChaCha20",
         "Layer 2 — Playfair", "Layer 1 — Vigenere"]
    )
    posisi = [body.index(label) for label in urutan]
    assert posisi == sorted(posisi)

    tabel = _trace_tables(body)
    assert len(tabel) == 4
    for potongan, batas in zip(tabel, [200, 100, 64, 64]):
        assert 0 < len(_baris_tabel(potongan)) <= batas

    if not enkripsi:
        # Tabel Vigenere adalah layer terakhir pada dekripsi.
        assert "".join(b[3] for b in _baris_tabel(tabel[3])) == pesan
