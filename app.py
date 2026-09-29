# app.py - Academic Evaluation Dashboard (Client-Server Architecture)
import io
import os
from pathlib import Path
import re
import pandas as pd
import requests
import streamlit as st

from components.header_card import render_student_header

# Import Modul Lokal dengan Fallback
try:
    from module.calculator import tentukan_predikat
except ImportError:

    def tentukan_predikat(ipk: float) -> str:
        if ipk >= 3.51:
            return "Dengan Pujian (Cum Laude)"
        elif ipk >= 3.00:
            return "Sangat Memuaskan"
        elif ipk >= 2.75:
            return "Memuaskan"
        else:
            return "Cukup"


try:
    from module.exporter import konversi_ke_excel
except ImportError:

    def konversi_ke_excel(df: pd.DataFrame) -> bytes:
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Transkrip")
        return output.getvalue()


try:
    from module.parser import proses_dokumen_pdf
except ImportError:
    proses_dokumen_pdf = None

try:
    from module.database import ambil_data_nilai, simpan_hasil_ekstraksi
except ImportError:
    simpan_hasil_ekstraksi = None
    ambil_data_nilai = None

# Konfigurasi API
API_HOST = os.getenv("API_HOST", "127.0.0.1")
API_PORT = os.getenv("API_PORT", "8000")
API_BASE_URL = f"http://{API_HOST}:{API_PORT}"

# 1. Konfigurasi Halaman Utama
st.set_page_config(
    page_title="Academic Evaluation Dashboard",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)


# 2. Load CSS Global
def load_css(css_file_path: str):
    path = Path(css_file_path)
    if path.is_file():
        with open(path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


load_css("assets/custom_style.css")

# 3. Inisialisasi Session State Profil
if "profil" not in st.session_state:
    st.session_state["profil"] = {
        "npm": "50422999",
        "username": "vito_dev",
        "status": "Aktif",
    }


# 4. Fungsi Data Loader (Prioritas SQLite Lokal Hasil Import PDF)
def fetch_df_semua(npm: str) -> pd.DataFrame:
    # 1. Utamakan SQLite Lokal jika ada data hasil ekstraksi PDF
    if ambil_data_nilai:
        df_db = ambil_data_nilai(npm)
        if not df_db.empty:
            return df_db

    # 2. Jika SQLite lokal kosong, coba ambil dari FastAPI Backend
    api_url_npm = f"{API_BASE_URL}/mahasiswa/{npm}/nilai"
    try:
        response = requests.get(api_url_npm, timeout=3)
        if response.status_code == 200:
            data = response.json()
            if data:
                return pd.DataFrame(data)
    except Exception:
        pass

    st.caption("⚠️ *Mode Offline: Belum ada data PDF terimpor, menggunakan data cadangan.*")

    # 3. Fallback Dummy Data
    dummy_data = [
        {
            "id": 1,
            "no": 1,
            "kode": "INF101",
            "mata_kuliah": "Algoritma & Pemrograman",
            "sks": 3,
            "nilai": "A",
            "bobot": 4.0,
            "semester": 1,
        },
        {
            "id": 2,
            "no": 2,
            "kode": "INF102",
            "mata_kuliah": "Basis Data I",
            "sks": 3,
            "nilai": "A-",
            "bobot": 3.7,
            "semester": 1,
        },
        {
            "id": 3,
            "no": 3,
            "kode": "INF201",
            "mata_kuliah": "Pemrograman Orientasi Objek",
            "sks": 3,
            "nilai": "A",
            "bobot": 4.0,
            "semester": 2,
        },
        {
            "id": 4,
            "no": 4,
            "kode": "INF202",
            "mata_kuliah": "Struktur Data",
            "sks": 3,
            "nilai": "B+",
            "bobot": 3.3,
            "semester": 2,
        },
        {
            "id": 5,
            "no": 5,
            "kode": "INF301",
            "mata_kuliah": "Pemrograman Web & FastAPI",
            "sks": 4,
            "nilai": "A",
            "bobot": 4.0,
            "semester": 3,
        },
    ]
    return pd.DataFrame(dummy_data)


def simpan_profil_ke_backend(data_profil: dict):
    try:
        url_sync = f"{API_BASE_URL}/mahasiswa/sync"
        requests.post(url_sync, json=data_profil, timeout=3)
        st.sidebar.success("✅ Profil disinkronkan ke API!")
    except Exception:
        st.sidebar.warning("⚠️ API offline: Profil tersimpan di sesi lokal.")


# 5. Sidebar Navigasi & Import PDF (HANYA 1 KALI RENDER)
with st.sidebar:
    st.markdown(
        """
        <div class="sidebar-header">
            <div class="sidebar-brand">
                <span>🎓</span> Academic Portal
            </div>
        </div>
    """,
        unsafe_allow_html=True,
    )

    menu_selected = st.radio(
        "Navigasi Utama",
        options=[
            "📌 Dashboard Utama",
            "📊 Ringkasan Nilai",
            "⚙️ Pengaturan Akun",
        ],
        index=0,
        key="sidebar_menu_radio",
    )

    st.markdown("---")

    st.markdown("### 📥 Import Transkrip PDF")
    uploaded_pdf = st.file_uploader(
        "Unggah berkas PDF nilai:",
        type=["pdf"],
        help="Pilih file transkrip PDF untuk diekstrak profil dan nilainya.",
        key="pdf_uploader_sidebar_unique",
    )

    if uploaded_pdf is not None:
        try:
            if proses_dokumen_pdf:
                profil_pdf, daftar_nilai = proses_dokumen_pdf(uploaded_pdf)

                if not daftar_nilai:
                    st.sidebar.error("⚠️ PDF terbaca, tetapi tidak ada baris nilai.")
                else:
                    profil_baru = {
                        "npm": profil_pdf.get("npm", "50422999"),
                        "username": (profil_pdf.get("nama", "mahasiswa").lower().replace(" ", "_")[:12]),
                        "status": "Aktif",
                        "ipk_cetak": profil_pdf.get("ipk_dokumen", "-"),
                    }

                    # Simpan ke DB SQLite lokal
                    if simpan_hasil_ekstraksi:
                        simpan_hasil_ekstraksi(profil_pdf, daftar_nilai)

                    # Update Session State
                    st.session_state["profil"] = profil_baru
                    simpan_profil_ke_backend(profil_baru)

                    st.toast(
                        f"🎉 Berhasil memuat {len(daftar_nilai)} nilai untuk NPM {profil_baru['npm']}!",
                        icon="✅",
                    )
                    st.rerun()

        except Exception as e:
            st.sidebar.error(f"Gagal memproses PDF: {e}")

    st.markdown("---")
    st.caption("Academic Dashboard v2.0 • 2026")

# 6. Load Data Setelah Sidebar Memperbarui Profil
profil = st.session_state["profil"]
df_semua = fetch_df_semua(profil["npm"])

# 7. Tampilan Konten Utama
if menu_selected == "📌 Dashboard Utama":
    render_student_header(
        npm=profil["npm"],
        username=profil["username"],
        status_aktivasi=profil["status"],
    )

    st.markdown(
        '<div class="dashboard-title">Academic Evaluation Dashboard</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="dashboard-subtitle">Sistem pemantauan dan evaluasi nilai mahasiswa</div>',
        unsafe_allow_html=True,
    )

    # Metrik Global
    total_sks = int(df_semua["sks"].sum()) if not df_semua.empty else 0
    total_mutu = float((df_semua["sks"] * df_semua["bobot"]).sum()) if not df_semua.empty else 0.0
    ipk_hitung = round(total_mutu / total_sks, 2) if total_sks > 0 else 0.0
    predikat_teks = tentukan_predikat(ipk_hitung)

    # Rekap Per Semester
    if not df_semua.empty and "semester" in df_semua.columns:
        df_sem = (
            df_semua.groupby("semester")
            .agg(
                total_sks=("sks", "sum"),
                total_mutu=(
                    "sks",
                    lambda x: (x * df_semua.loc[x.index, "bobot"]).sum(),
                ),
                jumlah_matkul=("no", "count"),
            )
            .reset_index()
        )
        df_sem["ips"] = (df_sem["total_mutu"] / df_sem["total_sks"]).round(2)
    else:
        df_sem = pd.DataFrame(columns=["semester", "total_sks", "ips"])

    c1, c2, c3, c4 = st.columns(4)
    c1.metric(
        "IPK Kumulatif",
        f"{ipk_hitung:.2f}",
        delta=f"Dokumen: {profil.get('ipk_cetak', '-')}",
    )
    c2.metric("Total SKS Tuntas", f"{total_sks} SKS")
    c3.metric("Total Mata Kuliah", f"{len(df_semua)} Matkul")
    c4.metric("Predikat Kelulusan", predikat_teks)

    st.divider()

    tab_analisis, tab_filter_crud, tab_simulasi, tab_ekspor = st.tabs(
        [
            "📊 Analitik Tren & Sebaran",
            "📋 Eksplorasi & Simulasi Nilai (CRUD API)",
            "🎯 Perencana Target IPK (What-If)",
            "📥 Pusat Unduhan",
        ]
    )

    with tab_analisis:
        col_g1, col_g2 = st.columns([3, 2])
        with col_g1:
            st.markdown("**Tren Fluktuasi IPS Antarsemester**")
            if not df_sem.empty:
                df_line = df_sem[["semester", "ips"]].copy()
                df_line["Label"] = "Semester " + df_line["semester"].astype(str)
                st.line_chart(df_line.set_index("Label")[["ips"]], width="stretch")
            else:
                st.info("Belum ada data semester.")

        with col_g2:
            st.markdown("**Ringkasan Beban & Indeks Prestasi**")
            st.dataframe(
                df_sem[["semester", "total_sks", "ips"]],
                column_config={
                    "semester": "Semester",
                    "total_sks": "Beban SKS",
                    "ips": "IPS",
                },
                hide_index=True,
                width="stretch",
            )

        st.markdown("**Distribusi Mutu Nilai**")
        if not df_semua.empty and "nilai" in df_semua.columns:
            st.bar_chart(df_semua["nilai"].value_counts().sort_index(), color="#2563EB")

    with tab_filter_crud:
        f1, f2 = st.columns([1, 2])
        with f1:
            opsi_sem = ["Semua Semester"] + (
                sorted(df_semua["semester"].unique().tolist()) if not df_semua.empty else []
            )
            filter_sem = st.selectbox("Filter Semester:", opsi_sem)
        with f2:
            cari_matkul = st.text_input(
                "🔍 Cari Mata Kuliah / Kode:",
                placeholder="Ketik nama atau kode mata kuliah...",
            )

        df_tampil = df_semua.copy()
        if filter_sem != "Semua Semester" and not df_tampil.empty:
            df_tampil = df_tampil[df_tampil["semester"] == filter_sem]
        if cari_matkul and not df_tampil.empty:
            pola = cari_matkul.strip().lower()
            df_tampil = df_tampil[
                df_tampil["mata_kuliah"].str.lower().str.contains(pola)
                | df_tampil["kode"].str.lower().str.contains(pola)
            ]

        st.caption(f"Menampilkan **{len(df_tampil)}** dari total **{len(df_semua)}** mata kuliah.")
        if not df_tampil.empty:
            st.dataframe(
                df_tampil[["semester", "no", "kode", "mata_kuliah", "sks", "nilai", "bobot"]],
                column_config={
                    "semester": "Sem",
                    "no": "No",
                    "kode": "Kode",
                    "mata_kuliah": "Nama Mata Kuliah",
                    "sks": "SKS",
                    "nilai": "Nilai",
                    "bobot": "Bobot",
                },
                hide_index=True,
                width="stretch",
            )

        with st.expander("🛠️ Form Simulasi Perbaikan Nilai (Update via REST API)", expanded=False):
            if not df_semua.empty and "id" in df_semua.columns:
                opsi_pilihan = {
                    f"Sem {r['semester']} | {r['kode']} - {r['mata_kuliah']} (Nilai: {r['nilai']})": r["id"]
                    for _, r in df_semua.iterrows()
                }
                if opsi_pilihan:
                    label_terpilih = st.selectbox("Pilih Mata Kuliah:", list(opsi_pilihan.keys()))
                    id_edit = opsi_pilihan[label_terpilih]
                    data_target = df_semua[df_semua["id"] == id_edit].iloc[0]

                    e1, e2, e3 = st.columns([2, 1, 1])
                    with e1:
                        st.write(f"Mata Kuliah: **{data_target['mata_kuliah']}** ({data_target['sks']} SKS)")
                    with e2:
                        nilai_baru = st.selectbox("Nilai Baru:", ["A", "B", "C", "D", "E"], index=0)
                    with e3:
                        st.write("")
                        st.write("")
                        if st.button("Kirim Update Nilai ke Server", type="primary"):
                            try:
                                res_update = requests.put(
                                    f"{API_BASE_URL}/nilai/{id_edit}",
                                    json={"nilai": nilai_baru},
                                    timeout=3,
                                )
                                if res_update.status_code == 200:
                                    st.success(f"Nilai berhasil diperbarui ke {nilai_baru}!")
                                    st.rerun()
                                else:
                                    st.error("Gagal memperbarui nilai di server backend.")
                            except Exception:
                                st.error("Server FastAPI offline. Tidak dapat mengirim data.")

    with tab_simulasi:
        st.subheader("🎯 Simulasi & Perencana Target IPK")
        st.write("Hitung berapa IPS yang harus kamu raih di semester depan untuk mencapai IPK impian.")

        col_s1, col_s2 = st.columns(2)
        with col_s1:
            st.info(f"Status Saat Ini:\n* **Total SKS Tuntas:** {total_sks} SKS\n* **IPK Riil:** {ipk_hitung:.2f}")
            rencana_sks = st.number_input(
                "Beban SKS Semester Depan:",
                min_value=1,
                max_value=24,
                value=20,
                step=1,
            )
            target_ipk_input = st.slider(
                "Target IPK Kelulusan / Akhir:",
                min_value=round(float(ipk_hitung), 2),
                max_value=4.00,
                value=min(4.00, round(float(ipk_hitung) + 0.1, 2)),
                step=0.01,
            )

            tombol_hitung = st.button("Hitung Kebutuhan IPS", type="primary", width="stretch")

        with col_s2:
            if tombol_hitung:
                payload_simulasi = {
                    "sks_lalu": total_sks,
                    "ipk_lalu": ipk_hitung,
                    "sks_rencana": rencana_sks,
                    "target_ipk": target_ipk_input,
                }
                try:
                    res_sim = requests.post(
                        f"{API_BASE_URL}/kalkulator/target-ipk",
                        json=payload_simulasi,
                        timeout=3,
                    )
                    if res_sim.status_code == 200:
                        data_sim = res_sim.json()
                        ips_butuh = data_sim["ips_dibutuhkan"]

                        if data_sim["tercapai"]:
                            st.success(f"### Target IPS Dibutuhkan: **{ips_butuh:.2f}**")
                            st.write(f"ℹ️ {data_sim['catatan']}")
                        else:
                            st.error(f"### Target IPS Dibutuhkan: **{ips_butuh:.2f}**")
                            st.warning(
                                "⚠️ Target tidak memungkinkan hanya dalam 1 semester ke depan"
                                " karena melampaui batas maksimal IPS (4.00)."
                            )
                    else:
                        st.error("Gagal memproses perhitungan simulasi dari API.")
                except requests.exceptions.ConnectionError:
                    st.error("Server FastAPI belum menyala.")

    with tab_ekspor:
        st.subheader("Ekspor Laporan Transkrip")
        if not df_semua.empty:
            df_unduh = df_semua[["semester", "no", "kode", "mata_kuliah", "sks", "nilai", "bobot"]].copy()

            col_dl1, col_dl2 = st.columns(2)
            with col_dl1:
                csv_data = df_unduh.to_csv(index=False).encode("utf-8")
                st.info("📄 Format CSV untuk integrasi analitik atau basis data.")
                st.download_button(
                    label="⬇️ Unduh Berkas CSV",
                    data=csv_data,
                    file_name=f"Transkrip_{profil['npm']}.csv",
                    mime="text/csv",
                    type="primary",
                )

            with col_dl2:
                try:
                    excel_data = konversi_ke_excel(df_unduh)
                    st.info("📊 Format Excel (.xlsx) transkrip akademik.")
                    st.download_button(
                        label="⬇️ Unduh Berkas Excel",
                        data=excel_data,
                        file_name=f"Transkrip_{profil['npm']}.xlsx",
                        mime=("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
                        type="primary",
                    )
                except Exception as ex:
                    st.warning(f"Gagal memproses ekspor Excel: {ex}")

elif menu_selected == "📊 Ringkasan Nilai":
    st.markdown(
        '<div class="dashboard-title">Ringkasan Nilai</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="dashboard-subtitle">Tinjauan singkat seluruh mata kuliah</div>',
        unsafe_allow_html=True,
    )
    st.dataframe(df_semua, use_container_width=True)

elif menu_selected == "⚙️ Pengaturan Akun":
    st.markdown(
        '<div class="dashboard-title">Pengaturan Akun</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="dashboard-subtitle">Kelola profil dan preferensi pengguna</div>',
        unsafe_allow_html=True,
    )

    with st.form("form_pengaturan_profil"):
        st.write("### Profil Mahasiswa")
        input_npm = st.text_input("NPM", value=profil["npm"])
        input_username = st.text_input("Username", value=profil["username"])
        input_status = st.selectbox(
            "Status Aktivasi",
            options=["Aktif", "Cuti", "Non-Aktif"],
            index=0 if profil["status"] == "Aktif" else 1,
        )

        simpan_profil = st.form_submit_button("💾 Simpan Perubahan Profil")
        if simpan_profil:
            profil_update = {
                "npm": input_npm,
                "username": input_username,
                "status": input_status,
            }
            st.session_state["profil"] = profil_update
            simpan_profil_ke_backend(profil_update)
            st.success("Profil berhasil diperbarui!")
            st.rerun()
