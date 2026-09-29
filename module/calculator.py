"""Modul kalkulasi akademik: konversi bobot mutu, kalkulasi IPK/IPS, dan predikat kelulusan."""

BOBOT_MUTU = {
    "A": 4.0,
    "A-": 3.7,
    "B+": 3.3,
    "B": 3.0,
    "B-": 2.7,
    "C+": 2.3,
    "C": 2.0,
    "D": 1.0,
    "E": 0.0,
}


def ambil_bobot(nilai: str) -> float:
    """Mengembalikan bobot angka dari huruf mutu nilai."""
    if not nilai:
        return 0.0
    return BOBOT_MUTU.get(str(nilai).strip().upper(), 0.0)


def hitung_ipk(daftar_matkul: list[dict]) -> float:
    """Menghitung IPK kumulatif dari daftar mata kuliah.

    Setiap item dict minimal memiliki key: 'sks' (int) dan 'nilai' (str).
    """
    if not daftar_matkul:
        return 0.0

    total_sks = sum(int(m.get("sks", 0)) for m in daftar_matkul)
    if total_sks == 0:
        return 0.0

    total_mutu = sum(int(m.get("sks", 0)) * ambil_bobot(m.get("nilai", "")) for m in daftar_matkul)
    return round(total_mutu / total_sks, 2)


def tentukan_predikat(ipk: float) -> str:
    """Menentukan predikat kelulusan berdasarkan standar yudisium."""
    if ipk >= 3.51:
        return "CumLaude 🏆"
    elif ipk >= 3.00:
        return "Sangat Memuaskan ⭐"
    elif ipk >= 2.75:
        return "Memuaskan 👍"
    return "Cukup ⚠️"


def hitung_target_ips(sks_lalu: int, ipk_lalu: float, sks_rencana: int, target_ipk: float) -> dict:
    """Menghitung IPS yang dibutuhkan untuk mencapai target IPK tertentu.

    Rumus: target_mutu_total = (sks_lalu + sks_rencana) * target_ipk
            mutu_lalu = sks_lalu * ipk_lalu
            ips_dibutuhkan = (target_mutu_total - mutu_lalu) / sks_rencana
    """
    if sks_rencana <= 0:
        raise ValueError("SKS rencana semester depan harus lebih dari 0.")
    if not (0.0 <= target_ipk <= 4.0):
        raise ValueError("Target IPK harus berada pada rentang 0.0 - 4.0.")

    mutu_lalu = sks_lalu * ipk_lalu
    sks_total_akhir = sks_lalu + sks_rencana
    mutu_total_target = sks_total_akhir * target_ipk

    mutu_dibutuhkan = mutu_total_target - mutu_lalu
    ips_dibutuhkan = round(mutu_dibutuhkan / sks_rencana, 2)

    tercapai = ips_dibutuhkan <= 4.00
    bisa_santai = ips_dibutuhkan <= 0.00

    return {
        "sks_total_nanti": sks_total_akhir,
        "ips_dibutuhkan": max(0.00, ips_dibutuhkan),
        "tercapai": tercapai,
        "catatan": (
            "Target realistis untuk dicapai."
            if tercapai and not bisa_santai
            else (
                "Target IPK sudah terlampaui bahkan tanpa nilai tambahan."
                if bisa_santai
                else ("Target tidak memungkinkan secara matematis (butuh IPS > 4.00).")
            )
        ),
    }
