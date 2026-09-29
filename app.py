# app.py - Academic Evaluation Dashboard (Client-Server Architecture)
import os
import pandas as pd
import requests
from pathlib import Path
import streamlit as st
from components.header_card import render_student_header
from module.calculator import tentukan_predikat
from module.exporter import konversi_ke_excel

API_HOST = os.getenv("API_HOST", "127.0.0.1")
API_PORT = os.getenv("API_PORT", "8000")
API_BASE_URL = f"http://{API_HOST}:{API_PORT}"

st.set_page_config(
    page_title="Academic Evaluation Dashboard",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)


# fungsi load css global
def load_css(css_file_path: str):
    path = Path(css_file_path)
    if path.is_file():
        with open(path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


load_css("assets/custom_stylee.css")

render_student_header(npm="50422999", username="vito_dev", status_aktivasi="Aktif")

st.markdown(
    '<div class="dashboard-title">Academic Evaluation Dashboard</div',
    unsafe_allow_html=True,
)
st.markdown(
    '<div class="dashboard-subtitle">Sistem pemantauan dan evaluasi nilai mahasiswa</div>',
    unsafe_allow_html=True,
)

st.success("✅ Day 1 Selesai: Struktur folder dan CSS Global berhasil dimuat!")
st.button("Uji Coba Animasi Tombol")

# SIDEBAR: UPLOAD, SEEDER & PROFIL VIA API
with st.sidebar:
    st.header("📂 Sumber Dokumen")
    berkas_pdf = st.file_uploader("Unggah PDF Transkrip / Rangkuman Nilai", type=["pdf"])

    if berkas_pdf:
        if st.button("Proses Dokumen via API", type="primary", width="stretch"):
            with st.spinner("Mengirim dan mengekstrak berkas di server backend..."):
                try:
                    files = {
                        "file": (
                            berkas_pdf.name,
                            berkas_pdf.getvalue(),
                            "application/pdf",
                        )
                    }
                    res = requests.post(f"{API_BASE_URL}/mahasiswa/unggah-pdf", files=files)
                    if res.status_code == 200:
                        st.sidebar.success(res.json().get("pesan", "Berhasil diekstraksi!"))
                        st.rerun()
                    else:
                        st.sidebar.error(f"Error {res.status_code}: {res.json().get('detail')}")
                except requests.exceptions.ConnectionError:
                    st.sidebar.error("Gagal terhubung ke server FastAPI. Pastikan server aktif!")

    if st.button("🧪 Muat Data Sampel (Demo Mode)", width="stretch"):
        with st.spinner("Menghubungi server untuk memuat data sampel..."):
            try:
                res_seed = requests.post(f"{API_BASE_URL}/sistem/seed-data")
                if res_seed.status_code == 200:
                    st.sidebar.success("Data sampel berhasil dimuat!")
                    st.rerun()
                else:
                    st.sidebar.error("Gagal memuat data sampel dari server.")
            except requests.exceptions.ConnectionError:
                st.sidebar.error("Server backend FastAPI belum aktif.")

    st.divider()

    # Ambil Profil dari Backend API
    profil = None
    try:
        res_profil = requests.get(f"{API_BASE_URL}/mahasiswa/profil")
        if res_profil.status_code == 200:
            profil = res_profil.json()
    except requests.exceptions.ConnectionError:
        st.sidebar.warning("Server FastAPI belum menyala.")

    if profil:
        st.header("👤 Profil Mahasiswa")
        st.markdown(f"**Nama:**\n{profil['nama']}")
        st.markdown(f"**NPM:** `{profil['npm']}`")
        st.markdown(f"**Jurusan:** {profil['jurusan']}")
        st.caption(f"IPK Dokumen: **{profil.get('ipk_cetak', '-')}**")
    else:
        st.info("Belum ada data mahasiswa tersimpan di server.")

    st.divider()
    st.caption("Academic Evaluation Dashboard • v2.0 (FastAPI Client)")

# MAIN DASHBOARD
st.title("🎓 Dashboard Evaluasi Akademik Mahasiswa")
st.caption("Frontend Terintegrasi dengan Backend FastAPI via REST Client")

if not profil:
    st.info("👋 Silakan pastikan server FastAPI aktif dan unggah berkas PDF atau klik Muat Data Sampel.")
    st.stop()

# Ambil Riwayat Nilai dari Backend API
res_nilai = requests.get(f"{API_BASE_URL}/mahasiswa/{profil['npm']}/nilai")
if res_nilai.status_code != 200 or not res_nilai.json():
    st.warning("Data mata kuliah belum tersedia di server.")
    st.stop()

df_semua = pd.DataFrame(res_nilai.json())

# Kalkulasi Metrik Global
total_sks = int(df_semua["sks"].sum())
total_mutu = float((df_semua["sks"] * df_semua["bobot"]).sum())
ipk_hitung = round(total_mutu / total_sks, 2) if total_sks > 0 else 0.0
predikat_teks = tentukan_predikat(ipk_hitung)

# Rekap Per Semester
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

# Kartu Metrik
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
        df_line = df_sem[["semester", "ips"]].copy()
        df_line["Label"] = "Semester " + df_line["semester"].astype(str)
        st.line_chart(df_line.set_index("Label")[["ips"]], width="stretch")

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
    st.bar_chart(df_semua["nilai"].value_counts().sort_index(), color="#29b5e8")

with tab_filter_crud:
    f1, f2 = st.columns([1, 2])
    with f1:
        opsi_sem = ["Semua Semester"] + sorted(df_semua["semester"].unique().tolist())
        filter_sem = st.selectbox("Filter Semester:", opsi_sem)
    with f2:
        cari_matkul = st.text_input(
            "🔍 Cari Mata Kuliah / Kode:",
            placeholder="Ketik nama atau kode mata kuliah...",
        )

    df_tampil = df_semua.copy()
    if filter_sem != "Semua Semester":
        df_tampil = df_tampil[df_tampil["semester"] == filter_sem]
    if cari_matkul:
        pola = cari_matkul.strip().lower()
        df_tampil = df_tampil[
            df_tampil["mata_kuliah"].str.lower().str.contains(pola) | df_tampil["kode"].str.lower().str.contains(pola)
        ]

    st.caption(f"Menampilkan **{len(df_tampil)}** dari total **{len(df_semua)}** mata kuliah.")
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
        opsi_pilihan = {
            f"Sem {r['semester']} | {r['kode']} - {r['mata_kuliah']} (Nilai: {r['nilai']})": r["id"]
            for _, r in df_semua.iterrows()
        }
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
                res_update = requests.put(
                    f"{API_BASE_URL}/nilai/{id_edit}",
                    json={"nilai": nilai_baru},
                )
                if res_update.status_code == 200:
                    st.success(f"Nilai berhasil diperbarui ke {nilai_baru}!")
                    st.rerun()
                else:
                    st.error("Gagal memperbarui nilai di server backend.")

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
                            "⚠️ Target tidak memungkinkan hanya dalam 1 semester ke depan karena melampaui batas maksimal IPS (4.00). Pertimbangkan menambah semester atau menyesuaikan target."
                        )
                else:
                    st.error(f"Error: {res_sim.json().get('detail', 'Gagal memproses perhitungan.')}")
            except requests.exceptions.ConnectionError:
                st.error("Server FastAPI belum menyala.")

with tab_ekspor:
    st.subheader("Ekspor Laporan Transkrip")
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
            st.info("📊 Format Excel (.xlsx) rapi dengan pemisahan sheet per semester.")
            st.download_button(
                label="⬇️ Unduh Berkas Excel",
                data=excel_data,
                file_name=f"Transkrip_{profil['npm']}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                type="primary",
            )
        except Exception:
            st.warning("Modul `openpyxl` belum terpasang untuk ekspor Excel.")
