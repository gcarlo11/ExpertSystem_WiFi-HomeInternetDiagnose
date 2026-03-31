from __future__ import annotations

import streamlit as st

from expert_system.rules import GEJALA_QUESTIONS, RIWAYAT_QUESTIONS
from expert_system.service import run_diagnosis


def _build_inference_flowchart(initial_facts: dict[str, str], output) -> str:
    lines = [
        "digraph InferenceFlow {",
        "rankdir=LR;",
        'node [shape=box, style="rounded,filled", fillcolor="#eef6ff", color="#376996", fontname="Helvetica"];',
        'start [label="Fakta Awal"];',
    ]

    # Tampilkan fakta awal yang bernilai YA/PERNAH agar diagram lebih ringkas.
    important_facts = [
        f"{k}={v}" for k, v in initial_facts.items() if v in {"YA", "PERNAH"}
    ]
    start_label = "\\n".join(important_facts) if important_facts else "Semua jawaban negatif"
    lines.append(f'startFacts [label="{start_label}", fillcolor="#f9fcff"];')
    lines.append("start -> startFacts;")

    prev_node = "startFacts"
    for idx, step in enumerate(output.result.fired_steps, start=1):
        cond = "\\n".join([f"{k}={v}" for k, v in step.conditions.items()])
        concl_key, concl_value = step.conclusion
        rule_node = f"rule{idx}"
        fact_node = f"fact{idx}"

        lines.append(f'{rule_node} [label="{step.rule_id}\\n{step.description}", fillcolor="#fff7e6", color="#b7791f"];')
        lines.append(f'{fact_node} [label="{concl_key}={concl_value}", fillcolor="#eafbea", color="#2f855a"];')
        lines.append(f'{prev_node} -> {rule_node} [label="{cond}"];')
        lines.append(f"{rule_node} -> {fact_node};")

        prev_node = fact_node

    lines.append(
        f'diagnosis [label="DIAGNOSA={output.diagnosis}", shape=ellipse, fillcolor="#f3e8ff", color="#6b46c1"];'
    )
    lines.append(f"{prev_node} -> diagnosis;")
    lines.append("}")
    return "\n".join(lines)


st.set_page_config(page_title="Sistem Pakar WiFi", page_icon="📶", layout="wide")
st.title("Sistem Pakar Diagnosis WiFi + Internet Rumah")
st.caption("Inferensi Forward Chaining berbasis Rule Set (Gejala, Riwayat, Target Diagnosa)")

st.markdown("### 1) Input Gejala")
col1, col2 = st.columns(2)

answers: dict[str, str] = {}

for idx, (key, question) in enumerate(GEJALA_QUESTIONS.items()):
    with col1 if idx % 2 == 0 else col2:
        label = f"{key} - {question}"
        value = st.radio(label, options=["YA", "TIDAK"], horizontal=True)
        answers[key] = value

st.markdown("### 2) Input Riwayat")
col3, col4 = st.columns(2)

for idx, (key, question) in enumerate(RIWAYAT_QUESTIONS.items()):
    with col3 if idx % 2 == 0 else col4:
        label = f"{key} - {question}"
        value = st.radio(label, options=["PERNAH", "TIDAK_PERNAH"], horizontal=True)
        answers[key] = value

if st.button("Jalankan Inferensi", type="primary"):
    output = run_diagnosis(answers)

    st.markdown("## Hasil Diagnosa")
    st.success(f"Target Diagnosa: {output.diagnosis}")
    st.info(output.diagnosis_detail)

    gejala = output.result.facts.get("GEJALA", "-")
    riwayat = output.result.facts.get("RIWAYAT", "-")

    st.write("### Ringkasan Fakta Turunan")
    st.write(f"- GEJALA: {gejala}")
    st.write(f"- RIWAYAT: {riwayat}")

    st.write("### Jejak Rule yang Tembak")
    if output.result.fired_steps:
        for step in output.result.fired_steps:
            cond = " AND ".join([f"{k}={v}" for k, v in step.conditions.items()])
            concl_key, concl_value = step.conclusion
            st.write(f"- {step.rule_id}: IF {cond} THEN {concl_key}={concl_value}")

        st.write("### Alur Inferensi (Forward Chaining)")
        st.graphviz_chart(_build_inference_flowchart(answers, output), use_container_width=True)

        st.write("### Timeline Inferensi")
        for idx, step in enumerate(output.result.fired_steps, start=1):
            concl_key, concl_value = step.conclusion
            cond = " AND ".join([f"{k}={v}" for k, v in step.conditions.items()])
            st.markdown(
                f"**Langkah {idx} - {step.rule_id}**  \n"
                f"Kondisi terpenuhi: `{cond}`  \n"
                f"Fakta baru: `{concl_key}={concl_value}`"
            )
    else:
        st.warning("Tidak ada rule yang terpicu. Periksa rule base atau input.")

    if output.result.conflicts:
        st.write("### Peringatan Konflik")
        for conflict in output.result.conflicts:
            st.error(conflict)

with st.expander("Lihat Input Fakta Awal"):
    st.json(answers)
