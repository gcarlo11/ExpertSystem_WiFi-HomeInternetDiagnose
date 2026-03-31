from __future__ import annotations

import streamlit as st

from expert_system.rules import GEJALA_QUESTIONS, RIWAYAT_QUESTIONS
from expert_system.service import run_diagnosis


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
    else:
        st.warning("Tidak ada rule yang terpicu. Periksa rule base atau input.")

    if output.result.conflicts:
        st.write("### Peringatan Konflik")
        for conflict in output.result.conflicts:
            st.error(conflict)

with st.expander("Lihat Input Fakta Awal"):
    st.json(answers)
