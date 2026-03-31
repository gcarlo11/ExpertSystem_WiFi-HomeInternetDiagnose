from __future__ import annotations

from .engine import Rule


GEJALA_QUESTIONS = {
    "G1": "Tidak bisa terhubung ke WiFi / SSID tidak terdeteksi",
    "G2": "Koneksi internet putus-putus / tidak stabil",
    "G3": "Kecepatan internet sangat lambat",
    "G4": "Muncul DNS error / website tidak dapat dibuka",
    "G5": "Semua perangkat di jaringan terdampak",
    "G6": "Lampu indikator router merah / router mati",
}

RIWAYAT_QUESTIONS = {
    "H1": "Riwayat ubah konfigurasi router / DNS",
    "H2": "Riwayat laporan gangguan ISP di area",
}

DIAGNOSIS_DETAILS = {
    "Masalah Perangkat Pengguna": (
        "Biasanya hanya satu perangkat bermasalah. "
        "Coba restart perangkat, update driver WiFi, lalu forget dan reconnect."
    ),
    "Masalah Konfigurasi Jaringan": (
        "Ada indikasi salah konfigurasi DNS/IP setelah perubahan setting. "
        "Set ulang ke DHCP otomatis dan verifikasi DNS."
    ),
    "Masalah Router / Access Point": (
        "Gangguan berada pada perangkat jaringan internal. "
        "Coba restart router, update firmware, dan cek kanal WiFi."
    ),
    "Gangguan ISP Ringan": (
        "Ada indikasi gangguan sisi ISP tetapi belum total. "
        "Coba DNS publik sementara, lalu laporkan ke ISP."
    ),
    "Kerusakan Hardware": (
        "Gejala berat tanpa indikasi gangguan area ISP. "
        "Periksa atau ganti modem/router."
    ),
    "Gangguan ISP Masif": (
        "Gangguan total dari sisi provider. "
        "Butuh tindak lanjut dari ISP/NOC dan menunggu pemulihan."
    ),
}


RULES_SET_2_GEJALA = [
    Rule(
        rule_id="R7",
        conditions={"G6": "YA"},
        conclusion=("GEJALA", "BERAT"),
        description="Jika router mati/merah maka gejala berat.",
    ),
    Rule(
        rule_id="R8",
        conditions={"G4": "TIDAK", "G5": "TIDAK", "G6": "TIDAK"},
        conclusion=("GEJALA", "RINGAN"),
        description="Jika tidak ada DNS issue, tidak massal, router normal maka gejala ringan.",
    ),
    Rule(
        rule_id="R9",
        conditions={"G4": "YA", "G5": "TIDAK", "G6": "TIDAK"},
        conclusion=("GEJALA", "SEDANG"),
        description="Jika ada DNS issue lokal, gejala sedang.",
    ),
    Rule(
        rule_id="R10",
        conditions={"G1": "TIDAK", "G2": "TIDAK", "G3": "TIDAK", "G5": "YA", "G6": "TIDAK"},
        conclusion=("GEJALA", "SEDANG"),
        description="Semua perangkat terdampak tanpa gejala G1/G2/G3, gejala sedang.",
    ),
    Rule(
        rule_id="R11",
        conditions={"G1": "YA", "G5": "YA", "G6": "TIDAK"},
        conclusion=("GEJALA", "BERAT"),
        description="Tidak bisa connect dan berdampak massal, gejala berat.",
    ),
    Rule(
        rule_id="R12",
        conditions={"G1": "TIDAK", "G2": "YA", "G5": "YA", "G6": "TIDAK"},
        conclusion=("GEJALA", "BERAT"),
        description="Koneksi intermittent massal, gejala berat.",
    ),
    Rule(
        rule_id="R13",
        conditions={"G1": "TIDAK", "G2": "TIDAK", "G3": "YA", "G5": "YA", "G6": "TIDAK"},
        conclusion=("GEJALA", "BERAT"),
        description="Sangat lambat dan massal, gejala berat.",
    ),
]

RULES_SET_3_RIWAYAT = [
    Rule(
        rule_id="R14",
        conditions={"H1": "TIDAK_PERNAH", "H2": "TIDAK_PERNAH"},
        conclusion=("RIWAYAT", "OK"),
        description="Tidak ada riwayat perubahan atau gangguan area.",
    ),
    Rule(
        rule_id="R15",
        conditions={"H1": "PERNAH"},
        conclusion=("RIWAYAT", "NOT_OK"),
        description="Ada riwayat perubahan konfigurasi.",
    ),
    Rule(
        rule_id="R16",
        conditions={"H2": "PERNAH"},
        conclusion=("RIWAYAT", "NOT_OK"),
        description="Ada riwayat gangguan ISP di area.",
    ),
]

RULES_SET_1_TARGET = [
    Rule(
        rule_id="R1",
        conditions={"GEJALA": "RINGAN", "RIWAYAT": "OK"},
        conclusion=("DIAGNOSA", "Masalah Perangkat Pengguna"),
        description="Gejala ringan + riwayat OK.",
    ),
    Rule(
        rule_id="R2",
        conditions={"GEJALA": "RINGAN", "RIWAYAT": "NOT_OK"},
        conclusion=("DIAGNOSA", "Masalah Konfigurasi Jaringan"),
        description="Gejala ringan + riwayat not OK.",
    ),
    Rule(
        rule_id="R3",
        conditions={"GEJALA": "SEDANG", "RIWAYAT": "OK"},
        conclusion=("DIAGNOSA", "Masalah Router / Access Point"),
        description="Gejala sedang + riwayat OK.",
    ),
    Rule(
        rule_id="R4",
        conditions={"GEJALA": "SEDANG", "RIWAYAT": "NOT_OK"},
        conclusion=("DIAGNOSA", "Gangguan ISP Ringan"),
        description="Gejala sedang + riwayat not OK.",
    ),
    Rule(
        rule_id="R5",
        conditions={"GEJALA": "BERAT", "RIWAYAT": "OK"},
        conclusion=("DIAGNOSA", "Kerusakan Hardware"),
        description="Gejala berat + riwayat OK.",
    ),
    Rule(
        rule_id="R6",
        conditions={"GEJALA": "BERAT", "RIWAYAT": "NOT_OK"},
        conclusion=("DIAGNOSA", "Gangguan ISP Masif"),
        description="Gejala berat + riwayat not OK.",
    ),
]

ALL_RULES = RULES_SET_2_GEJALA + RULES_SET_3_RIWAYAT + RULES_SET_1_TARGET
