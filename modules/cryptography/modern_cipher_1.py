"""
modules/cryptography/modern_cipher_1.py
────────────────────────────────────────
ChaCha20 Cipher (Modern Cipher #1)

Uses the cryptography library's ChaCha20 implementation.
Output is base64-encoded for text-safe storage.
Format: <nonce_hex>:<ciphertext_b64>
"""

import os
import base64
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms


def chacha20_encrypt(plaintext: str, key: bytes) -> str:
    """
    Encrypt *plaintext* with ChaCha20.

    Parameters
    ----------
    plaintext : str    UTF-8 text.
    key       : bytes  32-byte key.

    Returns
    -------
    str  "<nonce_hex>:<ciphertext_b64>"
    """
    if len(key) != 32:
        raise ValueError("ChaCha20 requires a 32-byte key.")

    nonce = os.urandom(16)  # ChaCha20 uses 16-byte nonce in cryptography lib
    cipher = Cipher(algorithms.ChaCha20(key, nonce), mode=None)
    encryptor = cipher.encryptor()
    ct = encryptor.update(plaintext.encode("utf-8")) + encryptor.finalize()

    return f"{nonce.hex()}:{base64.b64encode(ct).decode()}"


def chacha20_decrypt(token: str, key: bytes) -> str:
    """
    Decrypt a token produced by chacha20_encrypt().

    Parameters
    ----------
    token : str    "<nonce_hex>:<ciphertext_b64>"
    key   : bytes  32-byte key.

    Returns
    -------
    str  Plaintext.
    """
    if len(key) != 32:
        raise ValueError("ChaCha20 requires a 32-byte key.")

    nonce_hex, ct_b64 = token.split(":", 1)
    nonce = bytes.fromhex(nonce_hex)
    ct = base64.b64decode(ct_b64)

    cipher = Cipher(algorithms.ChaCha20(key, nonce), mode=None)
    decryptor = cipher.decryptor()
    plaintext_bytes = decryptor.update(ct) + decryptor.finalize()
    return plaintext_bytes.decode("utf-8")


def chacha20_encrypt_stages(plaintext: str, key: bytes, limit: int = 64) -> dict:
    """
    Enkripsi ChaCha20 sekaligus mengembalikan tahapan dan jejak per byte.

    Returns
    -------
    dict: {"final": str, "stages": list[dict]}
    """
    if len(key) != 32:
        raise ValueError("ChaCha20 requires a 32-byte key.")

    nonce = os.urandom(16)
    cipher = Cipher(algorithms.ChaCha20(key, nonce), mode=None)
    encryptor = cipher.encryptor()
    pt_bytes = plaintext.encode("utf-8")
    ct = encryptor.update(pt_bytes) + encryptor.finalize()
    final = f"{nonce.hex()}:{base64.b64encode(ct).decode()}"

    total = max(len(pt_bytes), len(ct))
    jejak = []
    for offset in range(min(total, limit)):
        sebelum = pt_bytes[offset] if offset < len(pt_bytes) else None
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
        "nama": "ChaCha20",
        "kode": "chacha20",
        "jenis": "modern",
        "input": plaintext,
        "output": final,
        "keterangan": (
            "Cipher stream; jejak per byte membandingkan byte plaintext dengan byte ciphertext. "
            "Nonce ditampilkan; kunci tidak ditampilkan."
        ),
        "parameter": [
            {"label": "Nonce", "nilai": nonce.hex()},
            {"label": "Panjang nonce", "nilai": "16 byte"},
            {"label": "Mode", "nilai": "stream"},
            {"label": "Padding", "nilai": "tidak ada"},
            {"label": "Ukuran data", "nilai": f"{len(pt_bytes)} byte"},
        ],
        "jejak": jejak,
        "jejak_total": total,
        "jejak_ditampilkan": len(jejak),
        "jejak_dipotong": len(jejak) < total,
        "catatan": catatan,
    }
    return {"final": final, "stages": [stage]}


def chacha20_decrypt_stages(token: str, key: bytes, limit: int = 64) -> dict:
    """
    Dekripsi ChaCha20 sekaligus mengembalikan tahapan dan jejak per byte kebalikannya.

    Returns
    -------
    dict: {"final": str, "stages": list[dict]}
    """
    if len(key) != 32:
        raise ValueError("ChaCha20 requires a 32-byte key.")

    nonce_hex, ct_b64 = token.split(":", 1)
    nonce = bytes.fromhex(nonce_hex)
    ct = base64.b64decode(ct_b64)

    cipher = Cipher(algorithms.ChaCha20(key, nonce), mode=None)
    decryptor = cipher.decryptor()
    plaintext_bytes = decryptor.update(ct) + decryptor.finalize()
    final = plaintext_bytes.decode("utf-8")

    total = max(len(ct), len(plaintext_bytes))
    jejak = []
    for offset in range(min(total, limit)):
        sebelum = ct[offset] if offset < len(ct) else None
        sesudah = plaintext_bytes[offset] if offset < len(plaintext_bytes) else None
        jejak.append({
            "sebelum": f"{sebelum:02x}" if sebelum is not None else "",
            "sesudah": f"{sesudah:02x}" if sesudah is not None else "",
        })

    catatan = (
        f"ditampilkan {len(jejak)} byte pertama dari {total} byte"
        if len(jejak) < total else ""
    )
    stage = {
        "nama": "ChaCha20",
        "kode": "chacha20",
        "jenis": "modern",
        "input": token,
        "output": final,
        "keterangan": (
            "Cipher stream; sebelum adalah byte ciphertext dan sesudah adalah byte plaintext. "
            "Nonce ditampilkan; kunci tidak ditampilkan."
        ),
        "parameter": [
            {"label": "Nonce", "nilai": nonce_hex},
            {"label": "Panjang nonce", "nilai": "16 byte"},
            {"label": "Mode", "nilai": "stream"},
            {"label": "Padding", "nilai": "tidak ada"},
            {"label": "Ukuran data", "nilai": f"{len(plaintext_bytes)} byte"},
        ],
        "jejak": jejak,
        "jejak_total": total,
        "jejak_ditampilkan": len(jejak),
        "jejak_dipotong": len(jejak) < total,
        "catatan": catatan,
    }
    return {"final": final, "stages": [stage]}
