import streamlit as st


def render_student_header(npm: str, username: str, status_aktivasi: str):
    """Menampilkan Banner Utama dan 3 Card Ringkasan Data Mahasiswa secara Horizontal."""

    st.markdown(
        """
        <div style="background: linear-gradient(135deg, #1E3A8A, #2563EB); padding: 24px; border-radius: 16px; color: white; margin-bottom: 24px; box-shadow: 0 10px 20px -5px rgba(37, 99, 235, 0.25);">
            <h2 style="margin: 0; font-weight: 700; font-size: 1.6rem; color: #FFFFFF;">Selamat Datang di Dashboard Evaluasi Akademik</h2>
            <p style="margin: 8px 0 0 0; opacity: 0.9; font-size: 0.95rem;">Pantau perkembangan nilai dan Indeks Prestasi (IP) secara terpusat dan real-time.</p>
        </div>
    """,
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(
            f"""
            <div class="student-card">
                <div class="card-label">NPM</div>
                <div class="card-value">{npm}</div>
            </div>
        """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            f"""
            <div class="student-card">
                <div class="card-label">Username</div>
                <div class="card-value">{username}</div>
            </div>
        """,
            unsafe_allow_html=True,
        )

    with col3:
        is_active = status_aktivasi.lower() == "aktif"
        badge_color = "#10B981" if is_active else "#EF4444"
        st.markdown(
            f"""
            <div class="student-card">
                <div class="card-label">Status Aktivasi</div>
                <div class="card-value" style="color: {badge_color};">
                    <span class="status-indicator" style="background-color: {badge_color};"></span>
                    {status_aktivasi.capitalize()}
                </div>
            </div>
        """,
            unsafe_allow_html=True,
        )
