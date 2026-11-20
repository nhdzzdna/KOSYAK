"""
modules/cryptography/classical_cipher_1.py
───────────────────────────────────────────
Vigenere Cipher (Classic Cipher #1)

Dua varian disediakan:

* ``vigenere_encrypt`` / ``vigenere_decrypt`` — varian printable ASCII yang
  dipakai layer pertama Super Encryption. Format lama dipertahankan agar data
  tersimpan tetap dapat didekripsi.
* ``vigenere_letter_encrypt`` / ``vigenere_letter_decrypt`` — varian klasik
  A-Z untuk alat Vigenere mandiri. Kunci hanya boleh huruf, sedangkan karakter
  bukan huruf pada teks dibiarkan dan tidak memajukan indeks kunci.
"""

import re


def is_valid_vigenere_key(key: str) -> bool:
    """True bila *key* hanya berisi huruf A-Z (tidak peka huruf besar/kecil)."""
    return bool(key) and re.fullmatch(r"[A-Za-z]+", key) is not None


def _letter_shifts(key: str) -> list[int]:
    if not is_valid_vigenere_key(key):
        raise ValueError("Vigenere key must contain letters A-Z only.")
    return [ord(c.upper()) - ord("A") for c in key]


def _key_stream(key: str, length: int):
    """Generate cycled key character indices (0-94 relative to ASCII 32)."""
    key_clean = [ord(c) - 32 for c in key if 32 <= ord(c) <= 126]
    if not key_clean:
        raise ValueError("Vigenere key must contain at least one printable ASCII character.")
    for i in range(length):
        yield key_clean[i % len(key_clean)]


def vigenere_encrypt(plaintext: str, key: str) -> str:
    """
    Encrypt *plaintext* with Vigenere cipher using *key*.

    Only printable ASCII characters (ord 32–126) are shifted;
    all other characters are passed through unchanged.

    Parameters
    ----------
    plaintext : str
    key       : str  Any printable ASCII string.

    Returns
    -------
    str  Ciphertext.
    """
    printable = [c for c in plaintext if 32 <= ord(c) <= 126]
    ks = _key_stream(key, len(printable))
    result = []
    ki = iter(ks)
    for ch in plaintext:
        if 32 <= ord(ch) <= 126:
            shift = next(ki)
            result.append(chr((ord(ch) - 32 + shift) % 95 + 32))
        else:
            result.append(ch)
    return "".join(result)


def vigenere_decrypt(ciphertext: str, key: str) -> str:
    """
    Decrypt *ciphertext* encrypted with vigenere_encrypt().

    Parameters
    ----------
    ciphertext : str
    key        : str  Same key used for encryption.

    Returns
    -------
    str  Plaintext.
    """
    printable = [c for c in ciphertext if 32 <= ord(c) <= 126]
    ks = _key_stream(key, len(printable))
    result = []
    ki = iter(ks)
    for ch in ciphertext:
        if 32 <= ord(ch) <= 126:
            shift = next(ki)
            result.append(chr((ord(ch) - 32 - shift) % 95 + 32))
        else:
            result.append(ch)
    return "".join(result)


def vigenere_letter_encrypt(plaintext: str, key: str) -> str:
    """
    Enkripsi *plaintext* dengan Vigenere klasik A-Z.

    Hanya huruf yang digeser dan huruf besar/kecil dipertahankan. Karakter
    bukan huruf (spasi, tanda baca, angka) dibiarkan dan tidak memajukan
    indeks kunci.
    """
    shifts = _letter_shifts(key)
    result = []
    index = 0
    for ch in plaintext:
        if "A" <= ch <= "Z":
            base = ord("A")
        elif "a" <= ch <= "z":
            base = ord("a")
        else:
            result.append(ch)
            continue
        shift = shifts[index % len(shifts)]
        result.append(chr((ord(ch) - base + shift) % 26 + base))
        index += 1
    return "".join(result)


def vigenere_letter_decrypt(ciphertext: str, key: str) -> str:
    """Kebalikan dari :func:`vigenere_letter_encrypt`."""
    shifts = _letter_shifts(key)
    result = []
    index = 0
    for ch in ciphertext:
        if "A" <= ch <= "Z":
            base = ord("A")
        elif "a" <= ch <= "z":
            base = ord("a")
        else:
            result.append(ch)
            continue
        shift = shifts[index % len(shifts)]
        result.append(chr((ord(ch) - base - shift) % 26 + base))
        index += 1
    return "".join(result)


def vigenere_letter_trace(text: str, key: str, decrypt: bool = False,
                          limit: int | None = None) -> tuple[list[dict], int]:
    """
    Jejak Vigenere klasik A-Z per karakter teks masukan.

    Baris memuat ``posisi``, ``asal``, ``kunci`` (huruf kunci yang dipakai,
    sesuai kunci yang diketik pengguna), dan ``hasil``. Untuk dekripsi,
    ``asal`` adalah ciphertext dan ``hasil`` adalah plaintext. Karakter bukan
    huruf tetap dicatat dengan kunci kosong agar gabungan ``hasil`` sama
    dengan keluaran penuh selama jejak tidak dipotong.

    Returns
    -------
    (list[dict], int)  Daftar jejak dan jumlah karakter seluruhnya.
    """
    shifts = _letter_shifts(key)
    keys = [chr(ord("A") + shift) for shift in shifts]
    result: list[dict] = []
    index = 0

    for posisi, ch in enumerate(text):
        if limit is not None and len(result) >= limit:
            break
        if "A" <= ch <= "Z":
            base = ord("A")
        elif "a" <= ch <= "z":
            base = ord("a")
        else:
            result.append({
                "posisi": posisi + 1,
                "asal": ch,
                "kunci": "",
                "hasil": ch,
            })
            continue
        huruf_kunci = keys[index % len(keys)]
        shift = shifts[index % len(shifts)]
        if decrypt:
            hasil = chr((ord(ch) - base - shift) % 26 + base)
        else:
            hasil = chr((ord(ch) - base + shift) % 26 + base)
        result.append({
            "posisi": posisi + 1,
            "asal": ch,
            "kunci": huruf_kunci,
            "hasil": hasil,
        })
        index += 1

    return result, len(text)
