# Sistem Pakar WiFi & Internet Rumah (Forward Chaining)

Proyek ini adalah implementasi tugas mata kuliah **Sistem Pakar** berbasis:
- Rule-based system
- Inferensi forward chaining
- Domain diagnosis WiFi & internet rumah

Rule base disusun dari dokumen yang Anda lampirkan:
- Rule Set 2: inferensi `GEJALA` dari 6 gejala biner (`G1..G6`)
- Rule Set 3: inferensi `RIWAYAT` dari 2 variabel riwayat (`H1..H2`)
- Rule Set 1: inferensi `DIAGNOSA` dari kombinasi `GEJALA` dan `RIWAYAT`

## 1. Struktur Proyek

```text
expert_system/
  __init__.py
  engine.py      # Mesin forward chaining
  rules.py       # Basis aturan (R7-R13, R14-R16, R1-R6)
  service.py     # Service inference siap pakai
app.py           # Aplikasi Streamlit
main.py          # Versi CLI (opsional untuk demo cepat)
requirements.txt
README.md
```

## 2. Konsep Forward Chaining yang Dipakai

Forward chaining bekerja dari fakta awal menuju kesimpulan:
1. Pengguna mengisi fakta awal (`G1..G6`, `H1..H2`).
2. Engine mengecek semua rule yang kondisi IF-nya terpenuhi.
3. Rule yang cocok akan menambahkan fakta baru (THEN) ke working memory.
4. Proses berulang sampai tidak ada fakta baru.
5. Fakta akhir `DIAGNOSA` menjadi output utama.

Secara sederhana:

```text
Fakta Awal -> Rule Gejala/Riwayat -> Fakta Turunan (GEJALA, RIWAYAT) -> Rule Target -> DIAGNOSA
```

## 3. Ringkasan Rule Base

### Rule Set 2 (Gejala)
- R7: IF `G6=YA` THEN `GEJALA=BERAT`
- R8: IF `G4=TIDAK` AND `G5=TIDAK` AND `G6=TIDAK` THEN `GEJALA=RINGAN`
- R9: IF `G4=YA` AND `G5=TIDAK` AND `G6=TIDAK` THEN `GEJALA=SEDANG`
- R10: IF `G1=TIDAK` AND `G2=TIDAK` AND `G3=TIDAK` AND `G5=YA` AND `G6=TIDAK` THEN `GEJALA=SEDANG`
- R11: IF `G1=YA` AND `G5=YA` AND `G6=TIDAK` THEN `GEJALA=BERAT`
- R12: IF `G1=TIDAK` AND `G2=YA` AND `G5=YA` AND `G6=TIDAK` THEN `GEJALA=BERAT`
- R13: IF `G1=TIDAK` AND `G2=TIDAK` AND `G3=YA` AND `G5=YA` AND `G6=TIDAK` THEN `GEJALA=BERAT`

### Rule Set 3 (Riwayat)
Catatan implementasi: variabel riwayat di dokumen (`R1`,`R2`) dinamai `H1`,`H2` di kode supaya tidak bentrok dengan ID rule.

- R14: IF `H1=TIDAK_PERNAH` AND `H2=TIDAK_PERNAH` THEN `RIWAYAT=OK`
- R15: IF `H1=PERNAH` THEN `RIWAYAT=NOT_OK`
- R16: IF `H2=PERNAH` THEN `RIWAYAT=NOT_OK`

### Rule Set 1 (Target Diagnosa)
- R1: IF `GEJALA=RINGAN` AND `RIWAYAT=OK` THEN `DIAGNOSA=Masalah Perangkat Pengguna`
- R2: IF `GEJALA=RINGAN` AND `RIWAYAT=NOT_OK` THEN `DIAGNOSA=Masalah Konfigurasi Jaringan`
- R3: IF `GEJALA=SEDANG` AND `RIWAYAT=OK` THEN `DIAGNOSA=Masalah Router / Access Point`
- R4: IF `GEJALA=SEDANG` AND `RIWAYAT=NOT_OK` THEN `DIAGNOSA=Gangguan ISP Ringan`
- R5: IF `GEJALA=BERAT` AND `RIWAYAT=OK` THEN `DIAGNOSA=Kerusakan Hardware`
- R6: IF `GEJALA=BERAT` AND `RIWAYAT=NOT_OK` THEN `DIAGNOSA=Gangguan ISP Masif`

## 4. Cara Menjalankan

## Prasyarat
- Python 3.10+ (disarankan 3.11/3.12)

## Install dependency

```bash
pip install -r requirements.txt
```

## Jalankan aplikasi Streamlit

```bash
streamlit run app.py
```

Setelah itu browser akan membuka halaman interaktif diagnosis.

## Jalankan versi CLI (opsional)

```bash
python main.py
```

## 5. Output yang Dihasilkan

Aplikasi menampilkan:
- Target diagnosa akhir
- Penjelasan rekomendasi tindakan
- Fakta turunan (`GEJALA`, `RIWAYAT`)
- Jejak rule yang ditembak (fired rules) untuk transparansi inferensi
- Peringatan konflik jika ada rule menghasilkan fakta bertentangan

## 6. Contoh Skenario Uji

Contoh input:
- G1=TIDAK
- G2=YA
- G3=TIDAK
- G4=TIDAK
- G5=YA
- G6=TIDAK
- H1=PERNAH
- H2=TIDAK_PERNAH

Inferensi:
- R6 -> GEJALA=BERAT
- R22 -> RIWAYAT=NOT_OK
- A6 -> DIAGNOSA=Gangguan ISP Masif