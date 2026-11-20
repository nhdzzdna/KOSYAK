"""
routes/crypto_routes.py
────────────────────────
Crypto Tools: uji setiap cipher secara individual dan Super Encryption.
Setiap operasi mengembalikan hasil sekaligus tabel jejak proses.
Pure Python, tanpa file I/O.
"""

import base64
import hashlib
import re

from flask import Blueprint, jsonify, render_template, request

import config
from routes.auth_routes import login_required
from modules.strings import MSG
from modules.cryptography.classical_cipher_1 import (
    is_valid_vigenere_key, vigenere_letter_encrypt, vigenere_letter_decrypt,
    vigenere_letter_trace,
)
from modules.cryptography.classical_cipher_2 import (
    playfair_encrypt, playfair_decrypt, playfair_encrypt_trace,
    playfair_decrypt_trace,
)
from modules.cryptography.modern_cipher_1    import chacha20_encrypt, chacha20_decrypt
from modules.cryptography.modern_cipher_2    import blowfish_encrypt, blowfish_decrypt
from modules.cryptography.super_encryption   import (
    super_encrypt_stages, super_decrypt_stages,
    _byte_trace, _catatan, _TRACE_LIMIT, _PLAYFAIR_TRACE_LIMIT,
    _MODERN_TRACE_LIMIT,
)

crypto_bp = Blueprint("crypto", __name__)

# Salt tetap untuk turunan kunci alat (domain separation antar penggunaan).
_TOOL_KDF_SALT = b"cryptix-crypto-tools-v1"

_NAMA_CIPHER = {
    "vigenere": "Vigenere",
    "playfair": "Playfair",
    "chacha20": "ChaCha20",
    "blowfish": "Blowfish-CBC",
}


def _wants_json() -> bool:
    """True bila pemanggil mengharapkan balasan JSON, bukan halaman HTML."""
    if request.is_json:
        return True
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return True
    penerima = request.accept_mimetypes
    return (
        penerima.best_match(["text/html", "application/json"]) == "application/json"
        and penerima["application/json"] > penerima["text/html"]
    )


def _tool_key(key: str) -> bytes:
    """
    Turunkan kunci 32 byte untuk alat kripto individual.

    Heksadesimal 64 digit dipakai langsung sebagai kunci mentah; teks lain
    diturunkan dengan PBKDF2-HMAC-SHA256 bersalt, bukan SHA-256 polos.
    Kunci turunan ini tidak pernah dimasukkan ke stage/jejak.
    """
    k = key.strip()
    if re.fullmatch(r"[0-9a-fA-F]{64}", k):
        return bytes.fromhex(k)
    if not k:
        raise ValueError("Kunci tidak boleh kosong.")
    return hashlib.pbkdf2_hmac(
        config.PBKDF2_HASH_ALGO,
        k.encode("utf-8"),
        _TOOL_KDF_SALT,
        config.SUPER_ENC_PBKDF2_ITERATIONS,
        dklen=32,
    )


def _stage(nama: str, kode: str, jenis: str, masukan: str, hasil: str,
           keterangan: str, jejak: list[dict], total: int,
           parameter: list[dict] | None = None, satuan: str = "") -> dict:
    """Bentuk satu stage dengan metadata pemotongan jejak yang seragam."""
    return {
        "nama": nama,
        "kode": kode,
        "jenis": jenis,
        "input": masukan,
        "output": hasil,
        "keterangan": keterangan,
        "parameter": parameter or [],
        "jejak": jejak,
        "jejak_total": total,
        "jejak_ditampilkan": len(jejak),
        "jejak_dipotong": len(jejak) < total,
        "catatan": _catatan(total, len(jejak), satuan),
    }


def _judul_tahapan(cipher: str, enkripsi: bool) -> tuple[str, str]:
    """Judul panel dan satuan badge untuk satu cipher atau Super."""
    if cipher == "super":
        return MSG.CRYPTO_TAHAPAN_SUPER, MSG.CRYPTO_LABEL_LAYER
    aksi = MSG.CRYPTO_AKSI_ENKRIPSI if enkripsi else MSG.CRYPTO_AKSI_DEKRIPSI
    return (
        MSG.CRYPTO_TAHAPAN_TUNGGAL.format(nama=_NAMA_CIPHER[cipher], aksi=aksi),
        MSG.CRYPTO_LABEL_LANGKAH,
    )


def _stage_vigenere(masukan: str, hasil: str, key: str, enkripsi: bool) -> dict:
    """Satu stage Vigenere; huruf kunci yang dipakai berasal dari input pengguna."""
    jejak, total = vigenere_letter_trace(
        masukan, key, decrypt=not enkripsi, limit=_TRACE_LIMIT
    )
    return _stage(
        nama=_NAMA_CIPHER["vigenere"],
        kode="vigenere",
        jenis="vigenere",
        masukan=masukan,
        hasil=hasil,
        keterangan=(
            MSG.CRYPTO_STAGE_VIGENERE_ENCRYPT if enkripsi
            else MSG.CRYPTO_STAGE_VIGENERE_DECRYPT
        ),
        jejak=jejak,
        total=total,
    )


def _stage_playfair(masukan: str, hasil: str, key: str, enkripsi: bool) -> dict:
    """Satu stage Playfair lengkap dengan ringkasan persiapan teks."""
    if enkripsi:
        jejak, total = playfair_encrypt_trace(
            masukan, key, limit=_PLAYFAIR_TRACE_LIMIT
        )
    else:
        jejak, total = playfair_decrypt_trace(
            masukan, key, limit=_PLAYFAIR_TRACE_LIMIT
        )
    parameter = [
        {"label": MSG.CRYPTO_LABEL_PERSIAPAN, "nilai": MSG.CRYPTO_PLAYFAIR_PERSIAPAN},
        {
            "label": MSG.CRYPTO_LABEL_PENGISI,
            "nilai": (
                MSG.CRYPTO_PLAYFAIR_ISI_ENKRIPSI if enkripsi
                else MSG.CRYPTO_PLAYFAIR_ISI_DEKRIPSI
            ),
        },
    ]
    return _stage(
        nama=_NAMA_CIPHER["playfair"],
        kode="playfair",
        jenis="playfair",
        masukan=masukan,
        hasil=hasil,
        keterangan=(
            MSG.CRYPTO_STAGE_PLAYFAIR_ENCRYPT if enkripsi
            else MSG.CRYPTO_STAGE_PLAYFAIR_DECRYPT
        ),
        jejak=jejak,
        total=total,
        parameter=parameter,
        satuan="pasangan",
    )


def _stage_modern(cipher: str, token: str, masukan: str, hasil: str,
                  enkripsi: bool) -> dict:
    """
    Satu stage ChaCha20/Blowfish dengan jejak per byte dari hasil nyata.

    *token* adalah keluaran enkripsi (nonce/IV + base64) dan dipakai sebagai
    sumber byte ciphertext baik pada enkripsi maupun dekripsi.
    """
    awal, data_b64 = token.split(":", 1)
    data = base64.b64decode(data_b64)
    if enkripsi:
        sebelum, sesudah = masukan.encode("utf-8"), data
    else:
        sebelum, sesudah = data, hasil.encode("utf-8")
    jejak, total = _byte_trace(sebelum, sesudah, limit=_MODERN_TRACE_LIMIT)

    if cipher == "chacha20":
        parameter = [
            {"label": MSG.CRYPTO_LABEL_NONCE, "nilai": awal},
            {"label": MSG.CRYPTO_LABEL_PANJANG_NONCE, "nilai": MSG.CRYPTO_NILAI_16_BYTE},
            {"label": MSG.CRYPTO_LABEL_MODE, "nilai": MSG.CRYPTO_NILAI_MODE_STREAM},
            {"label": MSG.CRYPTO_LABEL_PADDING, "nilai": MSG.CRYPTO_NILAI_TANPA_PADDING},
        ]
        keterangan = (
            MSG.CRYPTO_STAGE_CHACHA_ENCRYPT if enkripsi
            else MSG.CRYPTO_STAGE_CHACHA_DECRYPT
        )
    else:
        parameter = [
            {"label": MSG.CRYPTO_LABEL_IV, "nilai": awal},
            {"label": MSG.CRYPTO_LABEL_PANJANG_IV, "nilai": MSG.CRYPTO_NILAI_8_BYTE},
            {"label": MSG.CRYPTO_LABEL_MODE, "nilai": MSG.CRYPTO_NILAI_MODE_CBC},
            {"label": MSG.CRYPTO_LABEL_PADDING, "nilai": MSG.CRYPTO_NILAI_PKCS7},
            {"label": MSG.CRYPTO_LABEL_UKURAN_BLOK, "nilai": MSG.CRYPTO_NILAI_8_BYTE},
        ]
        keterangan = (
            MSG.CRYPTO_STAGE_BLOWFISH_ENCRYPT if enkripsi
            else MSG.CRYPTO_STAGE_BLOWFISH_DECRYPT
        )

    return _stage(
        nama=_NAMA_CIPHER[cipher],
        kode=cipher,
        jenis="modern",
        masukan=masukan,
        hasil=hasil,
        keterangan=keterangan,
        jejak=jejak,
        total=total,
        parameter=parameter,
        satuan="byte",
    )


@crypto_bp.route("/crypto-tools", methods=["GET", "POST"])
@login_required
def index():
    result = None
    error  = None
    stages = None
    status = 200

    if request.method == "POST":
        action     = request.form.get("action", "encrypt")   # encrypt / decrypt
        cipher     = request.form.get("cipher", "super")
        text       = request.form.get("text",       "")
        key        = request.form.get("key",        "")
        passphrase = request.form.get("passphrase", "")
        enkripsi   = action == "encrypt"

        try:
            if cipher == "vigenere":
                if not is_valid_vigenere_key(key):
                    error = MSG.CRYPTO_VIGENERE_KEY_INVALID
                    status = 400
                    if _wants_json():
                        return jsonify({"error": error}), status
                else:
                    result = (
                        vigenere_letter_encrypt(text, key) if enkripsi
                        else vigenere_letter_decrypt(text, key)
                    )
                    stages = [_stage_vigenere(text, result, key, enkripsi)]

            elif cipher == "playfair":
                result = (
                    playfair_encrypt(text, key) if enkripsi
                    else playfair_decrypt(text, key)
                )
                stages = [_stage_playfair(text, result, key, enkripsi)]

            elif cipher in ("chacha20", "blowfish"):
                bkey = _tool_key(key)
                if cipher == "chacha20":
                    result = (
                        chacha20_encrypt(text, bkey) if enkripsi
                        else chacha20_decrypt(text, bkey)
                    )
                else:
                    result = (
                        blowfish_encrypt(text, bkey) if enkripsi
                        else blowfish_decrypt(text, bkey)
                    )
                token = result if enkripsi else text
                stages = [_stage_modern(cipher, token, text, result, enkripsi)]

            elif cipher == "super":
                if not passphrase:
                    error = MSG.CRYPTO_PASSPHRASE_REQUIRED
                else:
                    detail = (
                        super_encrypt_stages(text, passphrase=passphrase) if enkripsi
                        else super_decrypt_stages(text, passphrase=passphrase)
                    )
                    result = detail["final"]
                    stages = detail["stages"]
            else:
                error = MSG.CRYPTO_UNKNOWN_CIPHER
        except Exception:
            error = MSG.CRYPTO_OPERATION_FAILED

    judul_tahapan = None
    satuan_tahapan = None
    if stages is not None:
        judul_tahapan, satuan_tahapan = _judul_tahapan(cipher, enkripsi)

    return render_template(
        "crypto_tools.html",
        result=result,
        error=error,
        stages=stages,
        stages_judul=judul_tahapan,
        stages_satuan=satuan_tahapan,
    ), status
