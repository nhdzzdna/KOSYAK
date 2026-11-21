"""
modules/cryptography/modern_cipher_2.py
────────────────────────────────────────
Blowfish Cipher in CBC mode with PKCS#7 padding (Modern Cipher #2)

Uses PyCryptodome's Blowfish implementation.
Output format: "<iv_hex>:<ciphertext_b64>"
"""

import os
import base64

from Crypto.Cipher import Blowfish as _Blowfish
from Crypto.Util.Padding import pad, unpad


_BLOCK_SIZE = 8   # Blowfish block size in bytes


def blowfish_encrypt(plaintext: str, key: bytes) -> str:
    """
    Encrypt *plaintext* with Blowfish-CBC + PKCS#7 padding.

    Parameters
    ----------
    plaintext : str    UTF-8 text.
    key       : bytes  4–56 bytes key (we use 32 bytes).

    Returns
    -------
    str  "<iv_hex>:<ciphertext_b64>"
    """
    iv = os.urandom(_BLOCK_SIZE)
    cipher = _Blowfish.new(key[:56], _Blowfish.MODE_CBC, iv)  # key max 56 bytes
    ct = cipher.encrypt(pad(plaintext.encode("utf-8"), _BLOCK_SIZE))
    return f"{iv.hex()}:{base64.b64encode(ct).decode()}"


def blowfish_decrypt(token: str, key: bytes) -> str:
    """
    Decrypt a token produced by blowfish_encrypt().

    Parameters
    ----------
    token : str    "<iv_hex>:<ciphertext_b64>"
    key   : bytes  Same key used for encryption.

    Returns
    -------
    str  Plaintext.
    """
    iv_hex, ct_b64 = token.split(":", 1)
    iv = bytes.fromhex(iv_hex)
    ct = base64.b64decode(ct_b64)

    cipher = _Blowfish.new(key[:56], _Blowfish.MODE_CBC, iv)
    plaintext_bytes = unpad(cipher.decrypt(ct), _BLOCK_SIZE)
    return plaintext_bytes.decode("utf-8")


def blowfish_encrypt_stages(plaintext: str, key: bytes, limit: int = 64) -> dict:
    """
    Enkripsi Blowfish-CBC sekaligus mengembalikan tahapan dan jejak per byte.

    Returns
    -------
    dict: {"final": str, "stages": list[dict]}
    """
    iv = os.urandom(_BLOCK_SIZE)
    cipher = _Blowfish.new(key[:56], _Blowfish.MODE_CBC, iv)
    pt_bytes = plaintext.encode("utf-8")
    padded = pad(pt_bytes, _BLOCK_SIZE)
    ct = cipher.encrypt(padded)
    final = f"{iv.hex()}:{base64.b64encode(ct).decode()}"

    total = max(len(padded), len(ct))
    jejak = []
    for offset in range(min(total, limit)):
        sebelum = padded[offset] if offset < len(padded) else None
        sesudah = ct[offset] if offset < len(ct) else None
        jejak.append({
            "sebelum": f"{sebelum:02x}" if sebelum is not None else "",
            "sesudah": f"{sesudah:02x}" if sesudah is not None else "",
        })

    catatan = (
        f"ditampilkan {len(jejak)} byte pertama dari {total} byte"
        if len(jejak) < total else ""
    )
    stage = {
        "nama": "Blowfish-CBC",
        "kode": "blowfish",
        "jenis": "modern",
        "input": plaintext,
        "output": final,
        "keterangan": (
            "Cipher blok mode CBC dengan padding PKCS#7; jejak per byte membandingkan "
            "plaintext setelah padding dengan ciphertext. IV ditampilkan; kunci tidak ditampilkan."
        ),
        "parameter": [
            {"label": "IV", "nilai": iv.hex()},
            {"label": "Panjang IV", "nilai": "8 byte"},
            {"label": "Mode", "nilai": "CBC"},
            {"label": "Padding", "nilai": "PKCS#7"},
            {"label": "Ukuran blok", "nilai": "8 byte"},
            {"label": "Jumlah blok", "nilai": f"{len(padded) // _BLOCK_SIZE} blok"},
        ],
        "jejak": jejak,
        "jejak_total": total,
        "jejak_ditampilkan": len(jejak),
        "jejak_dipotong": len(jejak) < total,
        "catatan": catatan,
    }
    return {"final": final, "stages": [stage]}


def blowfish_decrypt_stages(token: str, key: bytes, limit: int = 64) -> dict:
    """
    Dekripsi Blowfish-CBC sekaligus mengembalikan tahapan dan jejak per byte kebalikannya.

    Returns
    -------
    dict: {"final": str, "stages": list[dict]}
    """
    iv_hex, ct_b64 = token.split(":", 1)
    iv = bytes.fromhex(iv_hex)
    ct = base64.b64decode(ct_b64)

    cipher = _Blowfish.new(key[:56], _Blowfish.MODE_CBC, iv)
    decrypted_padded = cipher.decrypt(ct)
    pt_bytes = unpad(decrypted_padded, _BLOCK_SIZE)
    final = pt_bytes.decode("utf-8")

    total = max(len(ct), len(pt_bytes))
    jejak = []
    for offset in range(min(total, limit)):
        sebelum = ct[offset] if offset < len(ct) else None
        sesudah = pt_bytes[offset] if offset < len(pt_bytes) else None
        jejak.append({
            "sebelum": f"{sebelum:02x}" if sebelum is not None else "",
            "sesudah": f"{sesudah:02x}" if sesudah is not None else "",
        })

    catatan = (
        f"ditampilkan {len(jejak)} byte pertama dari {total} byte"
        if len(jejak) < total else ""
    )
    stage = {
        "nama": "Blowfish-CBC",
        "kode": "blowfish",
        "jenis": "modern",
        "input": token,
        "output": final,
        "keterangan": (
            "Dekripsi blok mode CBC dengan padding PKCS#7; sebelum adalah byte ciphertext "
            "dan sesudah adalah byte plaintext setelah padding dibuang. "
            "IV ditampilkan; kunci tidak ditampilkan."
        ),
        "parameter": [
            {"label": "IV", "nilai": iv_hex},
            {"label": "Panjang IV", "nilai": "8 byte"},
            {"label": "Mode", "nilai": "CBC"},
            {"label": "Padding", "nilai": "PKCS#7 (dihilangkan)"},
            {"label": "Ukuran blok", "nilai": "8 byte"},
            {"label": "Jumlah blok", "nilai": f"{len(ct) // _BLOCK_SIZE} blok"},
        ],
        "jejak": jejak,
        "jejak_total": total,
        "jejak_ditampilkan": len(jejak),
        "jejak_dipotong": len(jejak) < total,
        "catatan": catatan,
    }
    return {"final": final, "stages": [stage]}
