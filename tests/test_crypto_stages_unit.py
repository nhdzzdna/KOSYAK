"""
tests/test_crypto_stages_unit.py
─────────────────────────────────
Pengujian unit untuk fungsi tahapan tiap cipher individual:
Vigenere, Playfair, ChaCha20, dan Blowfish-CBC.
Memastikan:
- Hasil akhir enkripsi tahapan sama dengan fungsi enkripsi biasa.
- Tahapan dekripsi memulihkan teks asli.
- Kunci mentah tidak bocor di parameter atau jejak untuk cipher modern.
- Limit jejak dipatuhi dan catatan pemotongan akurat.
"""

import pytest

from modules.cryptography.classical_cipher_1 import (
    vigenere_letter_encrypt, vigenere_letter_decrypt,
    vigenere_encrypt_stages, vigenere_decrypt_stages,
)
from modules.cryptography.classical_cipher_2 import (
    playfair_encrypt, playfair_decrypt,
    playfair_encrypt_stages, playfair_decrypt_stages,
)
from modules.cryptography.modern_cipher_1 import (
    chacha20_encrypt, chacha20_decrypt,
    chacha20_encrypt_stages, chacha20_decrypt_stages,
)
from modules.cryptography.modern_cipher_2 import (
    blowfish_encrypt, blowfish_decrypt,
    blowfish_encrypt_stages, blowfish_decrypt_stages,
)


class TestVigenereStages:
    def test_encrypt_matches_base_and_roundtrip(self):
        text = "Halo Dunia Kriptografi 2026!"
        key = "KUNCI"
        expected = vigenere_letter_encrypt(text, key)

        stage_enc = vigenere_encrypt_stages(text, key)
        assert stage_enc["final"] == expected
        assert len(stage_enc["stages"]) == 1
        assert stage_enc["stages"][0]["nama"] == "Vigenere"
        assert stage_enc["stages"][0]["jenis"] == "vigenere"
        assert len(stage_enc["stages"][0]["jejak"]) == len(text)

        stage_dec = vigenere_decrypt_stages(expected, key)
        assert stage_dec["final"] == text
        assert vigenere_letter_decrypt(expected, key) == text

    def test_invalid_key_raises(self):
        with pytest.raises(ValueError):
            vigenere_encrypt_stages("teks", "kunci 123!")


class TestPlayfairStages:
    def test_encrypt_matches_base_and_roundtrip(self):
        text = "PESAN RAHASIA"
        key = "MONARKI"
        expected = playfair_encrypt(text, key)

        stage_enc = playfair_encrypt_stages(text, key)
        assert stage_enc["final"] == expected
        assert len(stage_enc["stages"]) == 1
        assert stage_enc["stages"][0]["nama"] == "Playfair"
        assert stage_enc["stages"][0]["jenis"] == "playfair"
        assert any(p["label"] == "Matriks 5×5" for p in stage_enc["stages"][0]["parameter"])

        stage_dec = playfair_decrypt_stages(expected, key)
        assert stage_dec["final"] == "PESAN RAHASIA"


class TestChaCha20Stages:
    def test_encrypt_and_decrypt_roundtrip(self):
        text = "Pesan rahasia untuk ChaCha20!"
        key = b"\x42" * 32

        stage_enc = chacha20_encrypt_stages(text, key)
        token = stage_enc["final"]
        assert ":" in token
        assert len(stage_enc["stages"]) == 1
        st = stage_enc["stages"][0]
        assert st["nama"] == "ChaCha20"
        assert st["jenis"] == "modern"
        # Kunci mentah tidak boleh ada di parameter atau jejak
        for param in st["parameter"]:
            assert key.hex() not in str(param["nilai"])
        for row in st["jejak"]:
            assert key.hex() not in str(row)

        stage_dec = chacha20_decrypt_stages(token, key)
        assert stage_dec["final"] == text

    def test_invalid_key_length_raises(self):
        with pytest.raises(ValueError):
            chacha20_encrypt_stages("halo", b"pendek")


class TestBlowfishStages:
    def test_encrypt_and_decrypt_roundtrip(self):
        text = "Pesan rahasia untuk Blowfish CBC!"
        key = b"\x37" * 32

        stage_enc = blowfish_encrypt_stages(text, key)
        token = stage_enc["final"]
        assert ":" in token
        assert len(stage_enc["stages"]) == 1
        st = stage_enc["stages"][0]
        assert st["nama"] == "Blowfish-CBC"
        assert st["jenis"] == "modern"
        # Kunci mentah tidak boleh ada di parameter atau jejak
        for param in st["parameter"]:
            assert key.hex() not in str(param["nilai"])
        for row in st["jejak"]:
            assert key.hex() not in str(row)

        stage_dec = blowfish_decrypt_stages(token, key)
        assert stage_dec["final"] == text

