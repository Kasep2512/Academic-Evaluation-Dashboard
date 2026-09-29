"""Modul operasi basis data SQLite untuk profil dan riwayat nilai mahasiswa."""

from pathlib import Path
import sqlite3
import pandas as pd

try:
    from module.calculator import BOBOT_MUTU
except ImportError:
    BOBOT_MUTU = {"A": 4.0, "B": 3.0, "C": 2.0, "D": 1.0, "E": 0.0}

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "akademik.db"


def buat_koneksi():
    """Membuat koneksi ke basis data SQLite."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def inisialisasi_database():
    """Membuat tabel profil_mahasiswa dan riwayat_nilai jika belum ada."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS profil_mahasiswa (
                npm TEXT PRIMARY KEY,
                nama TEXT,
                jurusan TEXT,
                ipk_dokumen TEXT
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS riwayat_nilai (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                npm TEXT,
                semester INTEGER,
                no INTEGER,
                kode TEXT,
                mata_kuliah TEXT,
                sks INTEGER,
                nilai TEXT,
                bobot REAL,
                FOREIGN KEY (npm) REFERENCES profil_mahasiswa (npm)
            )
        """)
        conn.commit()


def simpan_hasil_ekstraksi(profil: dict, daftar_nilai: list[dict]):
    """Menyimpan data hasil parsing PDF ke dalam database SQLite."""
    inisialisasi_database()
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO profil_mahasiswa (npm, nama, jurusan, ipk_dokumen)
            VALUES (?, ?, ?, ?)
            """,
            (
                profil.get("npm"),
                profil.get("nama"),
                profil.get("jurusan"),
                profil.get("ipk_dokumen"),
            ),
        )

        cursor.execute("DELETE FROM riwayat_nilai WHERE npm = ?", (profil.get("npm"),))

        query_insert_nilai = """
            INSERT INTO riwayat_nilai (npm, semester, no, kode, mata_kuliah, sks, nilai, bobot)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        data_rows = [
            (
                profil.get("npm"),
                n["semester"],
                n["no"],
                n["kode"],
                n["mata_kuliah"],
                n["sks"],
                n["nilai"],
                BOBOT_MUTU.get(n["nilai"].upper(), 0.0),
            )
            for n in daftar_nilai
        ]
        cursor.executemany(query_insert_nilai, data_rows)
        conn.commit()


def ambil_profil(npm: str = None):
    """Mengambil data profil mahasiswa terdaftar."""
    if not DB_PATH.exists():
        return None
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        if npm:
            cursor.execute(
                "SELECT npm, nama, jurusan, ipk_dokumen FROM profil_mahasiswa WHERE npm = ?",
                (npm,),
            )
        else:
            cursor.execute("SELECT npm, nama, jurusan, ipk_dokumen FROM profil_mahasiswa LIMIT 1")
        row = cursor.fetchone()
        return {"npm": row[0], "nama": row[1], "jurusan": row[2], "ipk_cetak": row[3]} if row else None


def ambil_data_nilai(npm: str) -> pd.DataFrame:
    """Mengambil seluruh riwayat nilai mahasiswa dalam bentuk DataFrame pandas."""
    if not DB_PATH.exists():
        return pd.DataFrame()
    with sqlite3.connect(DB_PATH) as conn:
        return pd.read_sql_query(
            """
            SELECT id, no, kode, mata_kuliah, sks, nilai, bobot, semester
            FROM riwayat_nilai
            WHERE npm = ?
            ORDER BY semester ASC, no ASC
            """,
            conn,
            params=(npm,),
        )


def update_nilai_matkul(id_matkul: int, nilai_baru: str):
    """Memperbarui nilai dan bobot mata kuliah tertentu untuk simulasi perbaikan nilai."""
    bobot_baru = BOBOT_MUTU.get(nilai_baru.upper(), 0.0)
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE riwayat_nilai SET nilai = ?, bobot = ? WHERE id = ?",
            (nilai_baru.upper(), bobot_baru, id_matkul),
        )
        conn.commit()


def jalankan_seeder():
    """Mengisi database dengan data pengujian dummy multi-semester."""
    profil_dummy = {
        "nama": "Mahasiswa Uji Coba",
        "npm": "50422999",
        "jurusan": "Sistem Informasi",
        "ipk_cetak": "3.85",
    }

    nilai_dummy = [
        {
            "semester": 1,
            "no": 1,
            "kode": "KD-011",
            "mata_kuliah": "Algoritma & Pemrograman 1",
            "sks": 3,
            "nilai": "A",
            "bobot": 4.0,
        },
        {
            "semester": 1,
            "no": 2,
            "kode": "KD-012",
            "mata_kuliah": "Pengantar Sistem Informasi",
            "sks": 3,
            "nilai": "A",
            "bobot": 4.0,
        },
        {
            "semester": 1,
            "no": 3,
            "kode": "KD-013",
            "mata_kuliah": "Matematika Diskrit",
            "sks": 3,
            "nilai": "B",
            "bobot": 3.0,
        },
        {
            "semester": 1,
            "no": 4,
            "kode": "KD-014",
            "mata_kuliah": "Bahasa Inggris 1",
            "sks": 2,
            "nilai": "A",
            "bobot": 4.0,
        },
        {
            "semester": 2,
            "no": 1,
            "kode": "KD-021",
            "mata_kuliah": "Struktur Data & Algoritma",
            "sks": 3,
            "nilai": "A",
            "bobot": 4.0,
        },
        {
            "semester": 2,
            "no": 2,
            "kode": "KD-022",
            "mata_kuliah": "Sistem Basis Data",
            "sks": 4,
            "nilai": "A",
            "bobot": 4.0,
        },
        {
            "semester": 2,
            "no": 3,
            "kode": "KD-023",
            "mata_kuliah": "Arsitektur & Organisasi Komputer",
            "sks": 3,
            "nilai": "B",
            "bobot": 3.0,
        },
        {
            "semester": 2,
            "no": 4,
            "kode": "KD-024",
            "mata_kuliah": "Statistika Komputasi",
            "sks": 3,
            "nilai": "A",
            "bobot": 4.0,
        },
        {
            "semester": 3,
            "no": 1,
            "kode": "KD-031",
            "mata_kuliah": "Pemrograman Berorientasi Objek",
            "sks": 3,
            "nilai": "A",
            "bobot": 4.0,
        },
        {
            "semester": 3,
            "no": 2,
            "kode": "KD-032",
            "mata_kuliah": "Rekayasa Perangkat Lunak",
            "sks": 3,
            "nilai": "A",
            "bobot": 4.0,
        },
        {
            "semester": 3,
            "no": 3,
            "kode": "KD-033",
            "mata_kuliah": "Sistem Operasi",
            "sks": 3,
            "nilai": "B",
            "bobot": 3.0,
        },
        {
            "semester": 3,
            "no": 4,
            "kode": "KD-034",
            "mata_kuliah": "Jaringan Komputer",
            "sks": 3,
            "nilai": "A",
            "bobot": 4.0,
        },
        {
            "semester": 4,
            "no": 1,
            "kode": "KD-041",
            "mata_kuliah": "Analisis & Desain Sistem",
            "sks": 3,
            "nilai": "A",
            "bobot": 4.0,
        },
        {
            "semester": 4,
            "no": 2,
            "kode": "KD-042",
            "mata_kuliah": "Administrasi Basis Data",
            "sks": 3,
            "nilai": "A",
            "bobot": 4.0,
        },
        {
            "semester": 4,
            "no": 3,
            "kode": "KD-043",
            "mata_kuliah": "Pengembangan Aplikasi Web",
            "sks": 3,
            "nilai": "A",
            "bobot": 4.0,
        },
        {
            "semester": 4,
            "no": 4,
            "kode": "KD-044",
            "mata_kuliah": "Metode Riset & Etika Profesi",
            "sks": 2,
            "nilai": "A",
            "bobot": 4.0,
        },
    ]

    simpan_hasil_ekstraksi(profil_dummy, nilai_dummy)
    return profil_dummy, len(nilai_dummy)
