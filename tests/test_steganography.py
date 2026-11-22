"""
tests/test_steganography.py
────────────────────────────
Uji LSB: round trip teks, penolakan gambar tanpa pesan, kapasitas
terlampaui, kunci salah, posisi bit tidak berurutan, batas dimensi,
penanganan muatan berkas lama yang tidak lagi didukung, serta rute web.
"""

import io
import os
import re
import struct
import tempfile
import zlib
from pathlib import Path

import pytest
from PIL import Image
import numpy as np

import config
from modules.strings import MSG
from modules.authentication import reauth
from modules.cryptography import session_keys
from modules.steganography.lsb import (
    HEADER_BITS, MAGIC, TYPE_FILE, VERSION,
    _embed_bits, _payload_positions, _seed, _stego_key,
    embed_message, extract_message, extract_payload,
    image_capacity,
)

DEK = bytes(range(32))
DEK_LAIN = bytes(range(1, 33))
PASSPHRASE = "frasa-sandi-tersembunyi"
ROOT = Path(__file__).resolve().parents[1]


def _make_white_png(path: str, width: int = 200, height: int = 200) -> None:
    arr = np.full((height, width, 3), 255, dtype=np.uint8)
    Image.fromarray(arr, "RGB").save(path, format="PNG")


class TestLSBUnit:
    def setup_method(self):
        self.tmpdir = tempfile.mkdtemp()
        self.src = os.path.join(self.tmpdir, "carrier.png")
        _make_white_png(self.src)

    def test_round_trip_teks_terenkripsi(self):
        out = os.path.join(self.tmpdir, "stego.png")
        msg = "Pesan rahasia LSB"
        result = embed_message(self.src, msg, out, master_key=DEK)
        assert result["success"] is True
        assert result["encrypted"] is True

        ext = extract_message(out, master_key=DEK)
        assert ext["success"] is True
        assert ext["message"] == msg
        assert ext["encrypted"] is True

    def test_round_trip_teks_tanpa_enkripsi(self):
        out = os.path.join(self.tmpdir, "plain.png")
        result = embed_message(self.src, "tampil polos", out,
                               master_key=DEK, encrypt=False)
        assert result["success"] is True
        assert result["encrypted"] is False

        ext = extract_message(out, master_key=DEK)
        assert ext["success"] is True
        assert ext["message"] == "tampil polos"
        assert ext["encrypted"] is False



    def test_round_trip_passphrase(self):
        out = os.path.join(self.tmpdir, "stego_pass.png")
        assert embed_message(self.src, "pesan sandi", out,
                             passphrase=PASSPHRASE)["success"]
        ext = extract_message(out, passphrase=PASSPHRASE)
        assert ext["success"] is True
        assert ext["message"] == "pesan sandi"

        assert extract_message(out, passphrase="salah")["success"] is False

    def test_gambar_tanpa_pesan_ditolak_jelas(self):
        plain = os.path.join(self.tmpdir, "biasa.png")
        _make_white_png(plain, 80, 80)
        result = extract_message(plain, master_key=DEK)
        assert result["success"] is False
        assert result["error"] == MSG.STEGO_NO_MESSAGE

    def test_kapasitas_terlampaui_ditolak(self):
        kecil = os.path.join(self.tmpdir, "kecil.png")
        _make_white_png(kecil, 10, 10)
        out = os.path.join(self.tmpdir, "kecil_stego.png")
        result = embed_message(kecil, "A" * 500, out, master_key=DEK)
        assert result["success"] is False
        assert "terlalu besar" in result["error"].lower()

    def test_kunci_salah_gagal(self):
        out = os.path.join(self.tmpdir, "stego_key.png")
        embed_message(self.src, "kunci asli", out, master_key=DEK)
        ext = extract_message(out, master_key=DEK_LAIN)
        assert ext["success"] is False
        assert ext["error"] in {MSG.STEGO_TAMPERED, MSG.STEGO_DECRYPT_FAILED}

    def test_tanpa_kunci_ditolak(self):
        out = os.path.join(self.tmpdir, "stego_noke.png")
        result = embed_message(self.src, "tanpa kunci", out)
        assert result["success"] is False
        assert result["error"] == MSG.STEGO_KEY_REQUIRED

        berkunci = os.path.join(self.tmpdir, "stego_ok.png")
        embed_message(self.src, "rahasia", berkunci, master_key=DEK)
        assert extract_message(berkunci)["error"] == MSG.STEGO_KEY_REQUIRED

    def test_posisi_bit_tidak_berurutan(self):
        out = os.path.join(self.tmpdir, "stego_pos.png")
        embed_message(self.src, "acakkan posisi", out, master_key=DEK)

        flat = np.array(Image.open(out).convert("RGB"), dtype=np.uint8).reshape(-1)
        header = np.packbits(flat[:HEADER_BITS] & np.uint8(1)).tobytes()
        magic, version, _type, length, crc = struct.unpack(">4sBBII", header)
        assert magic == MAGIC and version == VERSION

        # Bit muatan pada posisi berurutan setelah header tidak cocok CRC32.
        berurutan = np.packbits(
            (flat[HEADER_BITS:HEADER_BITS + length * 8] & np.uint8(1))
        ).tobytes()
        assert zlib.crc32(berurutan) & 0xFFFFFFFF != crc

        # Sedangkan posisi hasil acakan deterministik dan tidak berurutan.
        acak = np.concatenate(list(
            _payload_positions(HEADER_BITS, 1000, flat.size,
                               int.from_bytes(DEK[:8], "big"))
        ))
        assert not np.array_equal(acak, np.arange(HEADER_BITS, HEADER_BITS + 1000))
        acak_lagi = np.concatenate(list(
            _payload_positions(HEADER_BITS, 1000, flat.size,
                               int.from_bytes(DEK[:8], "big"))
        ))
        assert np.array_equal(acak, acak_lagi)

    def test_dimensi_lewat_batas_ditolak(self):
        lebar = os.path.join(self.tmpdir, "lebar.png")
        _make_white_png(lebar, 4001, 4)
        out = os.path.join(self.tmpdir, "lebar_stego.png")
        result = embed_message(lebar, "x", out, master_key=DEK)
        assert result["success"] is False
        assert "4000" in result["error"]
        assert "4000" in extract_message(lebar, master_key=DEK)["error"]

    def test_header_bermagic_cr_xs(self):
        out = os.path.join(self.tmpdir, "stego_magic.png")
        embed_message(self.src, "magic", out, master_key=DEK)
        flat = np.array(Image.open(out).convert("RGB"), dtype=np.uint8).reshape(-1)
        assert np.packbits(flat[:HEADER_BITS] & np.uint8(1)).tobytes()[:4] == MAGIC

    def test_image_capacity(self):
        info = image_capacity(self.src)
        assert info["width"] == 200 and info["height"] == 200
        assert info["capacity"] == (200 * 200 * 3 - HEADER_BITS) // 8
        assert "error" in image_capacity(os.path.join(self.tmpdir, "hilang.png"))

    def test_ekstrak_muatan_berkas_lama_tidak_crash(self):
        """Gambar lama bertipe berkas ditolak dengan pesan rapi, bukan crash."""
        out = _buat_stego_berkas_lama(
            self.src, b"isi berkas lama", "lama.bin", self.tmpdir,
            passphrase=PASSPHRASE,
        )
        hasil = extract_payload(out, passphrase=PASSPHRASE)
        assert hasil["success"] is False
        assert hasil["error"] == MSG.STEGO_FILE_PAYLOAD_UNSUPPORTED
        hasil_pesan = extract_message(out, passphrase=PASSPHRASE)
        assert hasil_pesan["success"] is False
        assert hasil_pesan["error"] == MSG.STEGO_FILE_PAYLOAD_UNSUPPORTED


def _buat_stego_berkas_lama(
    carrier_path: str, data: bytes, filename: str, tmpdir: str,
    passphrase: str | None = None,
) -> str:
    """Buat gambar stego bertipe berkas (format lama) untuk pengujian kompatibilitas."""
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM

    key = _stego_key(None, passphrase)
    img = Image.open(carrier_path).convert("RGB")
    pixels = np.array(img, dtype=np.uint8)
    flat = pixels.reshape(-1)

    plaintext = filename.encode("utf-8") + b"\x00" + data
    aad = MAGIC + bytes([VERSION, TYPE_FILE]) + len(plaintext).to_bytes(4, "big")
    nonce = b"\x01" * 12
    payload = nonce + AESGCM(key).encrypt(nonce, plaintext, aad)

    _embed_bits(flat, payload, TYPE_FILE, _seed(key))
    out = os.path.join(tmpdir, "stego_berkas_lama.png")
    Image.fromarray(pixels, "RGB").save(out, format="PNG")
    return out


# ── Rute web ─────────────────────────────────────────────────────────────────

@pytest.fixture()
def app(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DATABASE_PATH", str(tmp_path / "stego_uji.db"))
    monkeypatch.setattr(config, "ENCRYPTED_FILES_DIR", str(tmp_path / "encrypted_files"))
    monkeypatch.setattr(config, "STEGO_IMAGES_DIR", str(tmp_path / "stego_images"))
    monkeypatch.setattr(config, "TEMPORARY_FILES_DIR", str(tmp_path / "temporary_files"))
    from database.db import init_db, get_db
    init_db()
    with get_db() as db:
        db.execute(
            """INSERT OR IGNORE INTO users
               (id, username, email, password_hash, salt) VALUES (?,?,?,?,?)""",
            (1, "penguji", "penguji@contoh.test", "hash", "garam"),
        )
        db.commit()

    from app import create_app
    application = create_app()
    application.config["TESTING"] = True
    reauth.clear()
    return application


@pytest.fixture()
def client(app):
    c = app.test_client()
    with c.session_transaction() as sess:
        sess["user_id"] = 1
        sess["username"] = "penguji"
        sid = session_keys.create_session_id()
        sess["session_id"] = sid
        session_keys.put(sid, DEK)
    return c


def _csrf(client, halaman: str = "/steganography") -> str:
    page = client.get(halaman)
    assert page.status_code == 200
    match = re.search(r'name="csrf_token" value="([^"]+)"', page.get_data(as_text=True))
    assert match
    return match.group(1)


def _grant(client, scope: str, resource_id=None) -> str:
    """Terbitkan grant sekali pakai untuk sesi klien uji."""
    with client.session_transaction() as sess:
        sid = sess["session_id"]
    return reauth.issue_grant(sid, scope, resource_id)["token"]


def _gambar_png(ukuran: int = 120) -> bytes:
    arr = np.full((ukuran, ukuran, 3), (12, 90, 200), dtype=np.uint8)
    buf = io.BytesIO()
    Image.fromarray(arr, "RGB").save(buf, format="PNG")
    return buf.getvalue()


class TestRuteStego:
    def test_kapasitas_ditampilkan_sebelum_sisip(self, client):
        token = _csrf(client)
        resp = client.post("/steganography/capacity", data={
            "csrf_token": token,
            "carrier_image": (io.BytesIO(_gambar_png()), "pembawa.png"),
        }, content_type="multipart/form-data")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["capacity"] == (120 * 120 * 3 - HEADER_BITS) // 8

    def test_sisipkan_teks_lalu_unduh_png(self, client):
        token = _csrf(client)
        resp = client.post("/steganography/embed", data={
            "csrf_token": token,
            "carrier_image": (io.BytesIO(_gambar_png()), "foto.jpg"),
            "payload_type": "text",
            "message": "pesan tersembunyi",
            "passphrase": PASSPHRASE,
        }, content_type="multipart/form-data")
        assert resp.status_code == 302

        from database.db import get_db
        with get_db() as db:
            row = db.execute(
                "SELECT * FROM stego_images WHERE user_id=1"
            ).fetchone()
        assert row["has_encryption"] == 1

        unduhan = client.get(
            f"/steganography/download/{row['id']}",
            headers={"X-Reauth-Grant": _grant(client, "stego.download", row["id"])},
        )
        assert unduhan.status_code == 200
        disp = unduhan.headers.get("Content-Disposition", "")
        assert "foto.png" in disp and ".jpg" not in disp.split("filename=")[-1]

        from modules.blockchain.blockchain import add_block  # noqa: F401
        with get_db() as db:
            aksi = [b["action"] for b in db.execute(
                "SELECT action FROM blockchain_log ORDER BY block_index"
            )]
        assert "STEGO_EMBED" in aksi

    def test_sisip_tanpa_kunci_ditolak(self, client):
        token = _csrf(client)
        resp = client.post("/steganography/embed", data={
            "csrf_token": token,
            "carrier_image": (io.BytesIO(_gambar_png()), "pembawa.png"),
            "payload_type": "text",
            "message": "pesan tanpa kunci",
            "passphrase": "",
        }, content_type="multipart/form-data", follow_redirects=True)
        assert resp.status_code == 200
        assert MSG.STEGO_PASSPHRASE_REQUIRED in resp.get_data(as_text=True)

        from database.db import get_db
        with get_db() as db:
            jumlah = db.execute(
                "SELECT COUNT(*) AS c FROM stego_images"
            ).fetchone()["c"]
        assert jumlah == 0

    def test_ekstrak_gambar_tersimpan_tanpa_kunci_ditolak(self, client):
        token = _csrf(client)
        assert client.post("/steganography/embed", data={
            "csrf_token": token,
            "carrier_image": (io.BytesIO(_gambar_png()), "pembawa.png"),
            "payload_type": "text",
            "message": "rahasia tersimpan",
            "passphrase": PASSPHRASE,
        }, content_type="multipart/form-data").status_code == 302

        from database.db import get_db
        with get_db() as db:
            row = db.execute(
                "SELECT * FROM stego_images WHERE user_id=1"
            ).fetchone()

        token = _csrf(client)
        hasil = client.post(f"/steganography/extract/{row['id']}", data={
            "csrf_token": token,
            "reauth_grant": _grant(client, "stego.extract", row["id"]),
            "passphrase": "",
        })
        assert hasil.status_code == 400
        assert hasil.is_json
        data = hasil.get_json()
        assert data["success"] is False
        assert data["error"] == MSG.STEGO_PASSPHRASE_REQUIRED
        assert "rahasia tersimpan" not in hasil.get_data(as_text=True)

    def test_kunci_salah_lewat_endpoint_tersimpan(self, client):
        token = _csrf(client)
        assert client.post("/steganography/embed", data={
            "csrf_token": token,
            "carrier_image": (io.BytesIO(_gambar_png()), "pembawa.png"),
            "payload_type": "text",
            "message": "rahasia kunci salah",
            "passphrase": PASSPHRASE,
        }, content_type="multipart/form-data").status_code == 302

        from database.db import get_db
        with get_db() as db:
            row = db.execute(
                "SELECT * FROM stego_images WHERE user_id=1"
            ).fetchone()

        token = _csrf(client)
        hasil = client.post(f"/steganography/extract/{row['id']}", data={
            "csrf_token": token,
            "reauth_grant": _grant(client, "stego.extract", row["id"]),
            "passphrase": "kunci-yang-salah",
        })
        assert hasil.status_code == 400
        assert hasil.is_json
        data = hasil.get_json()
        assert data["success"] is False
        assert data["error"] in {
            MSG.STEGO_TAMPERED, MSG.STEGO_DECRYPT_FAILED,
        }
        assert "rahasia kunci salah" not in hasil.get_data(as_text=True)

    def test_ekstrak_unggahan_teks_dengan_passphrase(self, client, tmp_path):
        # Sisipkan memakai passphrase kustom di luar rute.
        pembawa = tmp_path / "pembawa.png"
        Image.new("RGB", (160, 160), color=(1, 2, 3)).save(pembawa, format="PNG")
        hasil = tmp_path / "hasil.png"
        assert embed_message(str(pembawa), "rahasia passphrase", str(hasil),
                             passphrase=PASSPHRASE)["success"]

        token = _csrf(client)
        resp = client.post("/steganography/extract-upload", data={
            "csrf_token": token,
            "reauth_grant": _grant(client, "stego.extract"),
            "stego_image": (io.BytesIO(hasil.read_bytes()), "stego.png"),
            "passphrase": PASSPHRASE,
        }, content_type="multipart/form-data", follow_redirects=True)
        assert resp.status_code == 200
        assert "rahasia passphrase" in resp.get_data(as_text=True)

        # Kunci kosong ditolak lebih awal dengan JSON rapi.
        token = _csrf(client)
        resp = client.post("/steganography/extract-upload", data={
            "csrf_token": token,
            "reauth_grant": _grant(client, "stego.extract"),
            "stego_image": (io.BytesIO(hasil.read_bytes()), "stego.png"),
            "passphrase": "",
        }, content_type="multipart/form-data")
        assert resp.status_code == 400
        assert resp.is_json
        data = resp.get_json()
        assert data["success"] is False
        assert data["error"] == MSG.STEGO_PASSPHRASE_REQUIRED
        assert "rahasia passphrase" not in resp.get_data(as_text=True)

    def test_unggahan_bukan_gambar_stego_ditolak(self, client):
        biasa = _gambar_png(60)
        token = _csrf(client)
        resp = client.post("/steganography/extract-upload", data={
            "csrf_token": token,
            "reauth_grant": _grant(client, "stego.extract"),
            "stego_image": (io.BytesIO(biasa), "biasa.png"),
            "passphrase": PASSPHRASE,
        }, content_type="multipart/form-data", follow_redirects=True)
        assert MSG.STEGO_NO_MESSAGE in resp.get_data(as_text=True)

    def test_ekstraksi_teks_lewat_json_dan_tampil_di_halaman(self, client):
        token = _csrf(client)
        resp = client.post("/steganography/embed", data={
            "csrf_token": token,
            "carrier_image": (io.BytesIO(_gambar_png()), "pembawa.png"),
            "payload_type": "text",
            "message": "pesan json tersembunyi",
            "passphrase": PASSPHRASE,
        }, content_type="multipart/form-data")
        assert resp.status_code == 302

        from database.db import get_db
        with get_db() as db:
            row = db.execute(
                "SELECT * FROM stego_images WHERE user_id=1"
            ).fetchone()

        token = _csrf(client)
        hasil = client.post(f"/steganography/extract/{row['id']}", data={
            "csrf_token": token,
            "reauth_grant": _grant(client, "stego.extract", row["id"]),
            "passphrase": PASSPHRASE,
        })
        assert hasil.status_code == 200
        assert hasil.is_json
        data = hasil.get_json()
        assert data["success"] is True
        assert data["type"] == "text"
        assert data["text"] == "pesan json tersembunyi"
        assert data["encrypted"] is True
        assert hasil.headers.get("X-Cryptix-Extract") == "text"

    def test_satu_kunci_teks_dipakai_ulang_lewat_rute(self, client):
        token = _csrf(client)
        resp = client.post("/steganography/embed", data={
            "csrf_token": token,
            "carrier_image": (io.BytesIO(_gambar_png()), "pembawa.png"),
            "payload_type": "text",
            "passphrase": PASSPHRASE,
            "message": "kunci teks bersama",
        }, content_type="multipart/form-data")
        assert resp.status_code == 302

        from database.db import get_db
        with get_db() as db:
            row = db.execute(
                "SELECT * FROM stego_images WHERE user_id=1"
            ).fetchone()
        token = _csrf(client)
        hasil = client.post(f"/steganography/extract/{row['id']}", data={
            "csrf_token": token,
            "reauth_grant": _grant(client, "stego.extract", row["id"]),
            "passphrase": PASSPHRASE,
        })
        assert hasil.status_code == 200
        assert hasil.is_json
        assert hasil.get_json()["text"] == "kunci teks bersama"

    def test_sisip_teks_dengan_passphrase_lalu_ekstrak(self, client):
        token = _csrf(client)
        resp = client.post("/steganography/embed", data={
            "csrf_token": token,
            "carrier_image": (io.BytesIO(_gambar_png()), "pembawa.png"),
            "payload_type": "text",
            "passphrase": PASSPHRASE,
            "message": "pesan dengan passphrase",
        }, content_type="multipart/form-data")
        assert resp.status_code == 302

        from database.db import get_db
        with get_db() as db:
            row = db.execute(
                "SELECT stored_name FROM stego_images WHERE user_id=1"
            ).fetchone()
        with open(os.path.join(config.STEGO_IMAGES_DIR, row["stored_name"]), "rb") as f:
            png_bytes = f.read()

        token = _csrf(client)
        benar = client.post("/steganography/extract-upload", data={
            "csrf_token": token,
            "reauth_grant": _grant(client, "stego.extract"),
            "stego_image": (io.BytesIO(png_bytes), "stego.png"),
            "passphrase": PASSPHRASE,
        }, content_type="multipart/form-data")
        assert benar.status_code == 200
        assert benar.get_json()["text"] == "pesan dengan passphrase"

        token = _csrf(client)
        salah = client.post("/steganography/extract-upload", data={
            "csrf_token": token,
            "reauth_grant": _grant(client, "stego.extract"),
            "stego_image": (io.BytesIO(png_bytes), "stego.png"),
            "passphrase": "passphrase-salah",
        }, content_type="multipart/form-data")
        assert salah.status_code == 400
        assert salah.is_json
        assert salah.get_json()["success"] is False
        assert salah.get_json()["error"] in {
            MSG.STEGO_TAMPERED, MSG.STEGO_DECRYPT_FAILED,
        }



    def test_kapasitas_terlampaui_lewat_rute(self, client):
        token = _csrf(client)
        resp = client.post("/steganography/embed", data={
            "csrf_token": token,
            "carrier_image": (io.BytesIO(_gambar_png(20)), "kecil.png"),
            "payload_type": "text",
            "message": "A" * 500,
            "passphrase": PASSPHRASE,
        }, content_type="multipart/form-data", follow_redirects=True)
        assert resp.status_code == 200
        assert "terlalu besar" in resp.get_data(as_text=True).lower()

    def test_passphrase_tidak_disimpan_di_session(self, client):
        token = _csrf(client)
        resp = client.post("/steganography/embed", data={
            "csrf_token": token,
            "carrier_image": (io.BytesIO(_gambar_png()), "pembawa.png"),
            "payload_type": "text",
            "passphrase": PASSPHRASE,
            "message": "jangan simpan passphrase",
        }, content_type="multipart/form-data")
        assert resp.status_code == 302
        with client.session_transaction() as sess:
            assert PASSPHRASE not in str(dict(sess))
        assert PASSPHRASE not in resp.headers.get("Set-Cookie", "")

    def test_halaman_memakai_js_eksternal_dan_panel_hasil(self, client):
        body = client.get("/steganography").get_data(as_text=True)
        assert 'id="stego-result"' in body
        assert "js/steganography.js" in body
        assert "onchange=" not in body
        assert "oninput=" not in body
        assert "onsubmit=" not in body
        assert "<script>" not in body
        assert 'type="text"' in body
        for terlarang in ("data-sg-kunci", "key_mode", "data-kx-sandi",
                          "STEGO_ACCOUNT_KEY_NOTE", "Kosongkan bila memakai kunci akun"):
            assert terlarang not in body, f"{terlarang} masih ada di halaman stego"

        js = (ROOT / "static" / "js" / "steganography.js").read_text(encoding="utf-8")
        for terlarang in ("key_mode", "data-sg-kunci", "master_key", "aturKunci",
                          "STEGO_ACCOUNT_KEY_NOTE"):
            assert terlarang not in js, f"{terlarang} masih ada di steganography.js"
        rute = (ROOT / "routes" / "stego_routes.py").read_text(encoding="utf-8")
        for terlarang in ("key_mode", "data-sg-kunci", "STEGO_ACCOUNT_KEY_NOTE",
                          "master_key="):
            assert terlarang not in rute, f"{terlarang} masih ada di stego_routes.py"

    def test_ekstrak_gambar_berkas_lama_mengembalikan_error_rapi(self, client, tmp_path):
        pembawa = tmp_path / "pembawa.png"
        Image.new("RGB", (160, 160), color=(255, 255, 255)).save(pembawa, format="PNG")
        stego_path = _buat_stego_berkas_lama(
            str(pembawa), b"isi lama", "lama.bin", str(tmp_path),
            passphrase=PASSPHRASE,
        )

        token = _csrf(client)
        resp = client.post("/steganography/extract-upload", data={
            "csrf_token": token,
            "reauth_grant": _grant(client, "stego.extract"),
            "stego_image": (io.BytesIO(open(stego_path, "rb").read()), "lama.png"),
            "passphrase": PASSPHRASE,
        }, content_type="multipart/form-data")
        assert resp.status_code == 400
        assert resp.is_json
        data = resp.get_json()
        assert data["success"] is False
        assert data["error"] == MSG.STEGO_FILE_PAYLOAD_UNSUPPORTED
