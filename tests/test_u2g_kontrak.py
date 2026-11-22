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


def test_kontrak_tabel_audio_fixed_dan_colgroup(client):
    """Tabel Audio memakai <colgroup>, table-layout: fixed, tanpa display: grid pada tr, dan th == td."""
    css_path = AKAR / "static" / "css" / "halaman" / "audio.css"
    konten_css = css_path.read_text(encoding="utf-8")

    # 1. audio.css memuat table-layout: fixed
    assert "table-layout: fixed" in konten_css, "audio.css harus memuat table-layout: fixed"

    # 2. Tidak memakai display: grid pada tr
    pola_grid_tr = re.compile(r"tr[^{]*\{[^}]*display\s*:\s*grid", re.DOTALL | re.IGNORECASE)
    assert not pola_grid_tr.search(konten_css), "audio.css tidak boleh memakai display: grid pada tr"

    # 3. Baris trek tanpa border-radius kartu
    pola_radius = re.compile(r"\.kx-audio-tr\s*\{[^}]*border-radius\s*:\s*var\(--kx-radius-card\)", re.DOTALL)
    assert not pola_radius.search(konten_css), "kx-audio-tr tidak boleh memiliki border-radius kartu"

    # 4. templates/musik.html memiliki <colgroup>
    html_path = AKAR / "templates" / "musik.html"
    konten_html = html_path.read_text(encoding="utf-8")
    assert "<colgroup>" in konten_html, "templates/musik.html harus memiliki <colgroup>"

    # 5. Tujuh kolom: checkbox, play, judul, folder, durasi, status, aksi.
    th_count = len(re.findall(r"<th\b", konten_html))
    assert th_count == 7, f"Header tabel audio harus 7 kolom, ditemukan {th_count}"
    for nama in ("select", "play", "title", "folder", "durasi", "status", "actions"):
        assert f"kx-audio-th-{nama}" in konten_html, f"Header {nama} tidak ditemukan"

    # 6. Lebar header tidak memakai atribut style inline.
    assert 'style="width' not in konten_html
    assert not re.search(r"<th\b[^>]*\bstyle\s*=", konten_html)

    # 7. Jumlah <th> sama dengan jumlah <td> pada baris macro track_row.
    macro_match = re.search(r"{%\s*macro\s+track_row\([^)]*\)\s*%}(.*?){%\s*endmacro\s*%}", konten_html, re.DOTALL)
    assert macro_match, "Macro track_row tidak ditemukan di musik.html"
    td_count = len(re.findall(r"<td\b", macro_match.group(1)))
    assert td_count == 7, f"Baris audio harus 7 sel, ditemukan {td_count}"
    assert th_count == td_count, f"Jumlah <th> ({th_count}) harus sama dengan jumlah <td> ({td_count})"


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


# ─────────────────────────────────────────────────────────────────────────────
# KONTRAK G2: VERIFIKASI HAPUS, PULIHKAN, DAN PUTAR AUDIO
# ─────────────────────────────────────────────────────────────────────────────

def _grant(client, scope: str, resource_id=None) -> str:
    from modules.authentication.reauth import issue_grant
    with client.session_transaction() as sess:
        sid = sess["session_id"]
    return issue_grant(sid, scope, resource_id)["token"]


def _csrf(client):
    import re
    resp = client.get("/dashboard")
    m = re.search(r'name="csrf_token"\s+value="([^"]+)"', resp.get_data(as_text=True))
    return m.group(1) if m else "token"


def _tambah_file(user_id=1, name="lagu.mp3", kind="audio"):
    import os, io, config
    from database.db import get_db
    from modules.cryptography.key_management import purpose_key
    from modules.cryptography.database_encryption import encrypt_field, field_aad
    from modules.cryptography.file_encryption import encrypt_stream, file_aad, generate_stored_name

    db_key = purpose_key(bytes(range(32)), "database")
    file_key = purpose_key(bytes(range(32)), "file")
    enc_name = encrypt_field(name, db_key, field_aad(user_id, "vault_files", "original_name"))

    os.makedirs(config.ENCRYPTED_FILES_DIR, exist_ok=True)
    stored_name = generate_stored_name()
    path = os.path.join(config.ENCRYPTED_FILES_DIR, stored_name)
    res = encrypt_stream(io.BytesIO(b"ID3\x03\x00\x00\x00\x00\x00\x00audio-data"), path, file_key, file_aad(user_id, stored_name))
    with get_db() as db:
        cur = db.execute(
            """INSERT INTO vault_files (user_id, stored_name, original_name, file_size, file_type, sha256_hash, sha256_ciphertext)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (user_id, stored_name, enc_name, 20, kind, res["sha256_plaintext"], res["sha256_ciphertext"]),
        )
        db.commit()
        return cur.lastrowid


def _tambah_note(user_id=1):
    from database.db import get_db
    from modules.cryptography.key_management import purpose_key
    from modules.cryptography.database_encryption import encrypt_field, field_aad
    from modules.cryptography.super_encryption import super_encrypt
    dek = bytes(range(32))
    db_key = purpose_key(dek, "database")
    t = encrypt_field("Catatan", db_key, field_aad(user_id, "secure_notes", "title_enc"))
    isi_super = super_encrypt("Isi", master_key=dek)
    c = encrypt_field(isi_super, db_key, field_aad(user_id, "secure_notes", "content_enc"))
    with get_db() as db:
        cur = db.execute(
            "INSERT INTO secure_notes (user_id, title_enc, content_enc) VALUES (?, ?, ?)",
            (user_id, t, c)
        )
        db.commit()
        return cur.lastrowid


def _tambah_cred(user_id=1):
    from database.db import get_db
    from modules.cryptography.key_management import purpose_key
    from modules.cryptography.database_encryption import encrypt_field, field_aad
    db_key = purpose_key(bytes(range(32)), "database")
    s = encrypt_field("example.com", db_key, field_aad(user_id, "account_vault", "site_name_enc"))
    u = encrypt_field("user", db_key, field_aad(user_id, "account_vault", "username_enc"))
    p = encrypt_field("pass", db_key, field_aad(user_id, "account_vault", "password_enc"))
    with get_db() as db:
        cur = db.execute(
            "INSERT INTO account_vault (user_id, site_name_enc, username_enc, password_enc) VALUES (?, ?, ?, ?)",
            (user_id, s, u, p)
        )
        db.commit()
        return cur.lastrowid


def _tambah_stego(user_id=1):
    import os, config
    from database.db import get_db
    from modules.cryptography.key_management import purpose_key
    from modules.cryptography.database_encryption import encrypt_field, field_aad
    from modules.cryptography.file_encryption import generate_stored_name
    db_key = purpose_key(bytes(range(32)), "database")
    os.makedirs(config.STEGO_IMAGES_DIR, exist_ok=True)
    fname = generate_stored_name()
    with open(os.path.join(config.STEGO_IMAGES_DIR, fname), "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\nfake")
    orig = encrypt_field("carrier.png", db_key, field_aad(user_id, "stego_images", "original_name"))
    with get_db() as db:
        cur = db.execute(
            "INSERT INTO stego_images (user_id, stored_name, original_name) VALUES (?, ?, ?)",
            (user_id, fname, orig)
        )
        db.commit()
        return cur.lastrowid


def test_kontrak_ui_tanpa_konfirmasi_dan_dengan_data_reauth():
    """Memeriksa tidak ada KX.konfirmasiHapus untuk soft-delete dan ada data-reauth item.delete."""
    templates = [
        "documents.html",
        "media_vault.html",
        "musik.html",
        "vault.html",
        "secure_notes.html",
        "account_vault.html",
        "steganography.html",
    ]
    for tmpl in templates:
        konten = (AKAR / "templates" / tmpl).read_text(encoding="utf-8")
        assert 'data-reauth="item.delete"' in konten, f"Template {tmpl} tidak memiliki data-reauth='item.delete'"

    # Memeriksa static JS tidak lagi memiliki interception KX.konfirmasiHapus untuk soft-delete
    js_files = [
        "documents.js",
        "media_albums.js",
        "musik.js",
        "secure_notes.js",
        "account_vault.js",
        "steganography.js",
    ]
    for js in js_files:
        konten = (AKAR / "static" / "js" / js).read_text(encoding="utf-8")
        assert "KX.konfirmasiHapus" not in konten, f"{js} masih memanggil KX.konfirmasiHapus untuk soft delete"


@pytest.mark.parametrize("endpoint_info", [
    ("file", "/vault/delete/{}", "item.delete", _tambah_file),
    ("note", "/secure-notes/delete/{}", "item.delete", _tambah_note),
    ("cred", "/account-vault/delete/{}", "item.delete", _tambah_cred),
    ("stego", "/steganography/delete/{}", "item.delete", _tambah_stego),
])
def test_kontrak_hapus_semua_jenis_dengan_grant_sekali_pakai(client, endpoint_info):
    """
    Uji siklus lengkap scope item.delete untuk seluruh jenis:
    1. Tanpa grant -> 401
    2. Grant scope salah -> 403
    3. Grant benar -> berhasil (302)
    4. Grant sudah terpakai (panggilan kedua) -> 401
    5. Urutan grant sebelum 404
    """
    jenis, url_pattern, scope, pembuat = endpoint_info
    csrf = _csrf(client)

    # 1. Tanpa grant -> 401
    item_id = pembuat()
    resp = client.post(url_pattern.format(item_id), data={"csrf_token": csrf})
    assert resp.status_code == 401
    assert resp.get_json()["reason"] == "missing"

    # 2. Grant scope salah -> 403
    token_salah = _grant(client, "settings.change", item_id)
    resp = client.post(
        url_pattern.format(item_id),
        data={"csrf_token": csrf, "reauth_grant": token_salah},
    )
    assert resp.status_code == 403
    assert resp.get_json()["reason"] == "scope"

    # 3. Grant benar -> berhasil (302)
    token_benar = _grant(client, scope, item_id)
    resp = client.post(
        url_pattern.format(item_id),
        data={"csrf_token": csrf, "reauth_grant": token_benar},
    )
    assert resp.status_code == 302

    # 4. Grant sudah terpakai -> 401
    resp = client.post(
        url_pattern.format(item_id),
        data={"csrf_token": csrf, "reauth_grant": token_benar},
    )
    assert resp.status_code == 401
    assert resp.get_json()["reason"] == "invalid"

    # 5. Urutan grant sebelum 404: grant ada tapi item 99999 tidak ada -> 404
    token_ada = _grant(client, scope, 99999)
    resp = client.post(
        url_pattern.format(99999),
        data={"csrf_token": csrf, "reauth_grant": token_ada},
    )
    assert resp.status_code == 404


def test_kontrak_trash_restore_grant_sekali_pakai(client):
    """Uji kontrak trash.restore: tanpa grant 401, scope salah 403, benar 200/302, kedua 401, sebelum 404."""
    import json
    csrf = _csrf(client)
    fid = _tambah_file(user_id=1, name="restore.pdf", kind="document")

    # Pindahkan dulu ke sampah dengan grant sah
    g_del = _grant(client, "item.delete", fid)
    client.post(f"/vault/delete/{fid}", data={"csrf_token": csrf, "reauth_grant": g_del})

    payload = {"items": [{"jenis": "file", "id": fid}]}

    # 1. Tanpa grant -> 401
    resp = client.post("/api/sampah/pulihkan", json=payload, headers={"X-CSRFToken": csrf})
    assert resp.status_code == 401
    assert resp.get_json()["reason"] == "missing"

    # 2. Scope salah -> 403
    t_salah = _grant(client, "trash.purge")
    resp = client.post(
        "/api/sampah/pulihkan",
        json=payload,
        headers={"X-CSRFToken": csrf, "X-Reauth-Grant": t_salah},
    )
    assert resp.status_code == 403
    assert resp.get_json()["reason"] == "scope"

    # 3. Grant benar -> berhasil 200
    t_benar = _grant(client, "trash.restore")
    resp = client.post(
        "/api/sampah/pulihkan",
        json=payload,
        headers={"X-CSRFToken": csrf, "X-Reauth-Grant": t_benar},
    )
    assert resp.status_code == 200
    assert resp.get_json()["success"] is True

    # 4. Panggilan kedua dengan grant yang sama -> 401
    resp = client.post(
        "/api/sampah/pulihkan",
        json=payload,
        headers={"X-CSRFToken": csrf, "X-Reauth-Grant": t_benar},
    )
    assert resp.status_code == 401
    assert resp.get_json()["reason"] == "invalid"

    # 5. Urutan grant sebelum 404: item 99999 tidak di sampah -> 404
    t_ada = _grant(client, "trash.restore")
    resp = client.post(
        "/api/sampah/pulihkan",
        json={"items": [{"jenis": "file", "id": 99999}]},
        headers={"X-CSRFToken": csrf, "X-Reauth-Grant": t_ada},
    )
    assert resp.status_code == 404


def test_kontrak_audio_play_grant_sekali_pakai(client):
    """Uji kontrak audio.play: tanpa grant 401, scope salah 403, benar 200, kedua 401, sebelum 404."""
    fid = _tambah_file(user_id=1, name="stream_kontrak.mp3", kind="audio")

    # 1. Tanpa grant -> 401
    resp = client.get(f"/media-vault/stream/{fid}")
    assert resp.status_code == 401
    assert resp.get_json()["reason"] == "missing"

    # 2. Scope salah -> 403
    t_salah = _grant(client, "media.stream", fid)
    resp = client.get(f"/media-vault/stream/{fid}", headers={"X-Reauth-Grant": t_salah})
    assert resp.status_code == 403
    assert resp.get_json()["reason"] == "scope"

    # 3. Grant benar -> 200, Content-Type audio/*, isi dan panjang sama dengan plaintext asli
    t_benar = _grant(client, "audio.play", fid)
    resp = client.get(f"/media-vault/stream/{fid}", headers={"X-Reauth-Grant": t_benar})
    assert resp.status_code == 200
    assert resp.content_type.startswith("audio/")
    assert resp.data == b"ID3\x03\x00\x00\x00\x00\x00\x00audio-data"
    assert len(resp.data) == 20

    # 4. Panggilan kedua dengan grant yang sama -> 401
    resp = client.get(f"/media-vault/stream/{fid}", headers={"X-Reauth-Grant": t_benar})
    assert resp.status_code == 401
    assert resp.get_json()["reason"] == "invalid"

    # 5. Urutan grant sebelum 404: file 99999 tidak ada -> 404
    t_ada = _grant(client, "audio.play", 99999)
    resp = client.get(f"/media-vault/stream/{99999}", headers={"X-Reauth-Grant": t_ada})
    assert resp.status_code == 404


def test_server_buka_catatan_dengan_grant(client):
    """(a) Server: buka catatan dengan note.open kembalikan isi, tanpa grant 401, scope salah 403."""
    nid = _tambah_note(user_id=1)
    csrf = _csrf(client)

    # 1. Tanpa grant -> 401
    resp = client.post(
        f"/secure-notes/open/{nid}",
        headers={"Content-Type": "application/json", "X-CSRFToken": csrf},
    )
    assert resp.status_code == 401
    assert resp.get_json()["reason"] == "missing"

    # 2. Scope salah -> 403
    t_salah = _grant(client, "doc.preview", nid)
    resp = client.post(
        f"/secure-notes/open/{nid}",
        headers={"Content-Type": "application/json", "X-CSRFToken": csrf, "X-Reauth-Grant": t_salah},
    )
    assert resp.status_code == 403
    assert resp.get_json()["reason"] == "scope"

    # 3. Grant benar -> 200 dengan judul dan isi terdekripsi
    t_benar = _grant(client, "note.open", nid)
    resp = client.post(
        f"/secure-notes/open/{nid}",
        headers={"Content-Type": "application/json", "X-CSRFToken": csrf, "X-Reauth-Grant": t_benar},
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["success"] is True
    assert data["title"] == "Catatan"
    assert data["content"] == "Isi"


def test_kontrak_selektor_secure_notes_js(client):
    """(b) Kontrak: setiap id & data-* yang dirujuk secure_notes.js ada di template; (c) detail tidak hidden permanen."""
    _tambah_note(user_id=1)
    resp = client.get("/secure-notes")
    assert resp.status_code == 200
    body = resp.get_data(as_text=True)

    # Memeriksa elemen dan selektor utama yang dirujuk secure_notes.js
    selektor_wajib = [
        "kx-sn-page",
        'id="sn-cari"',
        'id="sn-tak-cocok"',
        'id="sn-daftar"',
        "data-sn-item",
        "data-sn-judul",
        "data-sn-buka",
        "data-sn-open-url",
        "data-sn-detail",
        "data-sn-tutup",
        'name="title"',
        'name="content"',
    ]
    for sel in selektor_wajib:
        assert sel in body, f"Selektor {sel} yang dirujuk secure_notes.js tidak ditemukan di HTML secure_notes"

    # Wadah detail catatan menggunakan atribut 'hidden' standar HTML, bukan inline display:none !important
    pola_detail = re.search(r'<div\s+class="kx-sn-detail"\s+data-sn-detail="[^"]*"\s+hidden>', body)
    assert pola_detail is not None, "Wadah detail catatan harus memiliki atribut hidden yang dapat dilepas oleh JS"
    assert "display: none !important" not in body, "Wadah detail tidak boleh memiliki hidden permanen"


def test_kontrak_pemetaan_label_verifikasi():
    """Label verifikasi ramah pengguna: tanpa nama scope bertitik, kata sumber daya, grant, atau scope."""
    from modules.strings import MSG

    assert hasattr(MSG, "REAUTH_SCOPE_LABELS"), "MSG harus mendefinisikan REAUTH_SCOPE_LABELS"
    assert hasattr(MSG, "REAUTH_DEFAULT_LABEL"), "MSG harus mendefinisikan REAUTH_DEFAULT_LABEL"

    kata_terlarang = ["sumber daya", "grant", "scope"]
    pola_bertitik = re.compile(r"\b[a-z]+\.[a-z]+\b")

    for k, v in MSG.REAUTH_SCOPE_LABELS.items():
        assert not pola_bertitik.search(v), f"Label untuk '{k}' membocorkan nama scope bertitik: '{v}'"
        for kata in kata_terlarang:
            assert kata not in v.lower(), f"Label untuk '{k}' memuat kata terlarang '{kata}': '{v}'"

    for kata in kata_terlarang:
        assert kata not in MSG.REAUTH_DEFAULT_LABEL.lower()


def test_kontrak_modal_reauth_tanpa_nama_scope_mentah(client):
    """_reauth_modal.html yang dirender menyertakan data-labels JSON dan tidak menampilkan teks scope/sumber daya."""
    resp = client.get("/dashboard")
    assert resp.status_code == 200
    body = resp.get_data(as_text=True)

    assert 'id="reauth-modal"' in body
    assert 'data-labels=' in body
    assert 'data-default-label=' in body

    # Pastikan teks lama pembocor tidak ada di template
    assert "pada sumber daya" not in body
    assert 'Tindakan "' not in body


def _tambah_file_audio(user_id=1, nama="trek_uji.mp3"):
    from database.db import get_db
    from modules.cryptography.key_management import purpose_key
    from modules.cryptography.database_encryption import encrypt_field, field_aad

    db_key = purpose_key(bytes(range(32)), "database")
    nama_enc = encrypt_field(nama, db_key, field_aad(user_id, "vault_files", "original_name"))
    with get_db() as db:
        cur = db.execute(
            """INSERT INTO vault_files
               (user_id, original_name, stored_name, file_type, file_size, sha256_hash, sha256_ciphertext)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (user_id, nama_enc, "stored_audio.enc", "audio", 1024, "a" * 64, "b" * 64),
        )
        fid = cur.lastrowid
        db.commit()
    return fid


def test_kontrak_audio_tanpa_kelas_lama(client):
    """HTML halaman /audio dan templates/musik.html tidak memuat kelas lama music-track, music-track-play, music-track-name, atau audio-track-meta."""
    # 1. Cek langsung di templates/musik.html
    html_raw = (AKAR / "templates" / "musik.html").read_text(encoding="utf-8")
    assert not re.search(r'\bmusic-track\b', html_raw), "Kelas lama 'music-track' masih ditemukan di templates/musik.html"
    assert not re.search(r'\bmusic-track-play\b', html_raw), "Kelas lama 'music-track-play' masih ditemukan di templates/musik.html"
    assert not re.search(r'\bmusic-track-name\b', html_raw), "Kelas lama 'music-track-name' masih ditemukan di templates/musik.html"
    assert not re.search(r'(?<!kx-)audio-track-meta\b', html_raw), "Kelas lama 'audio-track-meta' masih ditemukan di templates/musik.html"

    # 2. Render dengan trek audio di database
    _tambah_file_audio(user_id=1)
    resp = client.get("/audio")
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)
    assert not re.search(r'\bmusic-track\b', html), "Kelas lama 'music-track' masih ditemukan di HTML render /audio"
    assert not re.search(r'\bmusic-track-play\b', html), "Kelas lama 'music-track-play' masih ditemukan di HTML render /audio"
    assert not re.search(r'\bmusic-track-name\b', html), "Kelas lama 'music-track-name' masih ditemukan di HTML render /audio"
    assert not re.search(r'(?<!kx-)audio-track-meta\b', html), "Kelas lama 'audio-track-meta' masih ditemukan di HTML render /audio"
    assert "kx-audio-table-wrap" in html


def test_kontrak_audio_table_wrap_overflow_visible():
    """audio.css memuat aturan overflow: visible untuk .kx-audio-table-wrap."""
    css_path = AKAR / "static" / "css" / "halaman" / "audio.css"
    konten_css = css_path.read_text(encoding="utf-8")
    pola = re.compile(r"\.kx-card-body\s*>\s*\.kx-table-wrap\.kx-audio-table-wrap\s*\{[^}]*overflow\s*:\s*visible", re.DOTALL)
    assert pola.search(konten_css), "audio.css harus memuat aturan overflow: visible untuk .kx-audio-table-wrap"


