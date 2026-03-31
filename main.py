from __future__ import annotations

from expert_system.service import run_diagnosis


def ask_yes_no(prompt: str) -> str:
    while True:
        answer = input(f"{prompt} [ya/tidak]: ").strip().lower()
        if answer in {"ya", "y"}:
            return "YA"
        if answer in {"tidak", "t"}:
            return "TIDAK"
        print("Input tidak valid, masukkan 'ya' atau 'tidak'.")


def ask_history(prompt: str) -> str:
    while True:
        answer = input(f"{prompt} [pernah/tidak]: ").strip().lower()
        if answer == "pernah":
            return "PERNAH"
        if answer == "tidak":
            return "TIDAK_PERNAH"
        print("Input tidak valid, masukkan 'pernah' atau 'tidak'.")


def main() -> None:
    print("=== Sistem Pakar WiFi & Internet Rumah (Forward Chaining) ===")

    initial_facts = {
        "G1": ask_yes_no("G1 Tidak bisa terhubung WiFi?"),
        "G2": ask_yes_no("G2 Koneksi internet putus-putus?"),
        "G3": ask_yes_no("G3 Kecepatan internet sangat lambat?"),
        "G4": ask_yes_no("G4 DNS error / web tidak bisa dibuka?"),
        "G5": ask_yes_no("G5 Semua perangkat terdampak?"),
        "G6": ask_yes_no("G6 Lampu router merah / router mati?"),
        "H1": ask_history("H1 Pernah ubah konfigurasi router/DNS?"),
        "H2": ask_history("H2 Pernah ada laporan gangguan ISP di area?"),
    }

    output = run_diagnosis(initial_facts)

    print("\n=== HASIL ===")
    print(f"GEJALA   : {output.result.facts.get('GEJALA', '-')}")
    print(f"RIWAYAT  : {output.result.facts.get('RIWAYAT', '-')}")
    print(f"DIAGNOSA : {output.diagnosis}")
    print(f"DETAIL   : {output.diagnosis_detail}")

    print("\nJejak rule fired:")
    for step in output.result.fired_steps:
        cond = " AND ".join([f"{k}={v}" for k, v in step.conditions.items()])
        target, value = step.conclusion
        print(f"- {step.rule_id}: IF {cond} THEN {target}={value}")

    if output.result.conflicts:
        print("\nPeringatan konflik:")
        for conflict in output.result.conflicts:
            print(f"- {conflict}")


if __name__ == "__main__":
    main()
