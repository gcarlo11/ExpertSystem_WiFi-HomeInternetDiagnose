from __future__ import annotations

import streamlit as st

from expert_system.rules import ALL_RULES, CF_USER_SCALE, GEJALA_QUESTIONS, RIWAYAT_QUESTIONS
from expert_system.service import run_diagnosis


def _build_inference_flowchart(initial_facts: dict[str, str], output) -> str:
    lines = [
        "digraph InferenceFlow {",
        "rankdir=LR;",
        'node [shape=box, style="rounded,filled", fillcolor="#eef6ff", color="#376996", fontname="Helvetica"];',
        'start [label="Fakta Awal"];',
    ]

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


QUESTION_FLOW = [
    {"key": key, "question": question, "kind": "gejala"}
    for key, question in GEJALA_QUESTIONS.items()
] + [
    {"key": key, "question": question, "kind": "riwayat"}
    for key, question in RIWAYAT_QUESTIONS.items()
]

CF_LABELS = [f"{label} ({value})" for label, value in CF_USER_SCALE]
CF_LABEL_TO_VALUE = {f"{label} ({value})": value for label, value in CF_USER_SCALE}
DEFAULT_CF_INDEX = next(
    (index for index, (label, _) in enumerate(CF_USER_SCALE) if label == "Mungkin"),
    0,
)

STATUS_LABELS = {
    "FIRED": "Terpenuhi dan firing",
    "NOT_MET": "Tidak terpenuhi",
    "CONFLICT": "Konflik",
    "ALREADY_TRUE": "Terpenuhi (fakta sudah ada)",
    "ALREADY_FIRED": "Sudah dieksekusi",
}


def _ensure_state() -> None:
    st.session_state.setdefault("flow_index", 0)
    st.session_state.setdefault("answers", {})
    st.session_state.setdefault("cf_user", {})


def _reset_state() -> None:
    keys_to_remove = [
        key for key in st.session_state.keys() if key.startswith(("ans_", "cf_"))
    ]
    for key in keys_to_remove:
        del st.session_state[key]
    st.session_state["flow_index"] = 0
    st.session_state["answers"] = {}
    st.session_state["cf_user"] = {}
    st.rerun()


st.set_page_config(page_title="Sistem Pakar WiFi", page_icon="📶", layout="wide")
st.title("Sistem Pakar Diagnosis WiFi + Internet Rumah")
st.caption("Inferensi Forward Chaining berbasis Rule Set (Gejala, Riwayat, Target Diagnosa)")

_ensure_state()

total_questions = len(QUESTION_FLOW)
flow_index = st.session_state["flow_index"]
answers: dict[str, str] = st.session_state["answers"]
cf_user: dict[str, float] = st.session_state["cf_user"]

st.markdown("### Pertanyaan")
progress_value = 1.0 if flow_index >= total_questions else (flow_index + 1) / total_questions
st.progress(progress_value)

if flow_index < total_questions:
    current = QUESTION_FLOW[flow_index]
    st.write(f"Pertanyaan {flow_index + 1} dari {total_questions}")
    st.write(f"{current['key']} - {current['question']}")

    answer_key = f"ans_{current['key']}"
    if answer_key not in st.session_state:
        st.session_state[answer_key] = "TIDAK"

    cf_value = 0.0

    if current["kind"] == "gejala":
        answer = st.radio("Jawaban", options=["TIDAK", "YA"], key=answer_key, horizontal=True)
        cf_key = f"cf_{current['key']}"
        if cf_key not in st.session_state:
            st.session_state[cf_key] = CF_LABELS[DEFAULT_CF_INDEX]
        if answer == "YA":
            cf_label = st.selectbox("Tingkat keyakinan", CF_LABELS, key=cf_key)
            cf_value = CF_LABEL_TO_VALUE[cf_label]
        else:
            st.caption("Tingkat keyakinan otomatis 0.0 karena jawaban TIDAK.")
    else:
        answer = st.radio("Jawaban", options=["TIDAK", "YA"], key=answer_key, horizontal=True)
        mapped_answer = "PERNAH" if answer == "YA" else "TIDAK_PERNAH"

    col_back, col_next, col_reset = st.columns([1, 1, 1])
    with col_back:
        back = st.button("Kembali", disabled=flow_index == 0)
    with col_next:
        next_step = st.button("Lanjut", type="primary")
    with col_reset:
        reset = st.button("Reset")

    if reset:
        _reset_state()

    if back:
        st.session_state["flow_index"] = max(flow_index - 1, 0)
        st.rerun()

    if next_step:
        if current["kind"] == "gejala":
            answers[current["key"]] = answer
            cf_user[current["key"]] = cf_value
        else:
            answers[current["key"]] = mapped_answer
        st.session_state["flow_index"] = flow_index + 1
        st.rerun()
else:
    st.success("Semua pertanyaan selesai. Silakan jalankan inferensi.")

    col_back, col_reset = st.columns([1, 1])
    with col_back:
        back = st.button("Kembali")
    with col_reset:
        reset = st.button("Reset")

    if reset:
        _reset_state()

    if back:
        st.session_state["flow_index"] = max(flow_index - 1, 0)
        st.rerun()

    if st.button("Jalankan Inferensi", type="primary"):
        output = run_diagnosis(answers, cf_user)

        st.markdown("## Hasil Diagnosa")
        st.success(f"Target Diagnosa: {output.diagnosis}")
        st.info(output.diagnosis_detail)

        st.write("### Tingkat Kepercayaan")
        st.metric("Tingkat Kepercayaan", f"{output.cf_percent:.1f}%")
        st.caption("CF(h,e)=MB x CFuser; CFcombine=CF1 + CF2 x (1 - CF1)")

        st.write("### Detail Certainty Factor")
        cf_rows = [
            {
                "Gejala": detail.gejala_id,
                "Bobot Gejala (MB)": detail.mb,
                "CF User": detail.cf_user,
                "CF Gejala": detail.cf_gejala,
            }
            for detail in output.cf_details
        ]
        st.dataframe(cf_rows, use_container_width=True)

        gejala = output.result.facts.get("GEJALA", "-")
        riwayat = output.result.facts.get("RIWAYAT", "-")

        st.write("### Ringkasan Fakta Turunan")
        st.write(f"- GEJALA: {gejala}")
        st.write(f"- RIWAYAT: {riwayat}")

        st.write("### Jejak Rule yang Firing")
        if output.result.fired_steps:
            for step in output.result.fired_steps:
                cond = " AND ".join([f"{k}={v}" for k, v in step.conditions.items()])
                concl_key, concl_value = step.conclusion
                st.write(
                    f"- {step.rule_id}: IF {cond} THEN {concl_key}={concl_value} ({step.description})"
                )

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

        st.write("### Pengecekan Rule (Forward Chaining)")
        checks = []
        for check in output.result.rule_checks:
            cond = " AND ".join([f"{k}={v}" for k, v in check.conditions.items()])
            concl_key, concl_value = check.conclusion
            missing = ", ".join(check.missing) if check.missing else "-"
            checks.append(
                {
                    "Iterasi": check.iteration,
                    "Rule": check.rule_id,
                    "Status": STATUS_LABELS.get(check.status, check.status),
                    "Kondisi": cond,
                    "Kesimpulan": f"{concl_key}={concl_value}",
                    "Tidak Terpenuhi": missing,
                    "Keterangan": check.description,
                }
            )
        if checks:
            st.dataframe(checks, use_container_width=True)

        if output.result.conflicts:
            st.write("### Peringatan Konflik")
            for conflict in output.result.conflicts:
                st.error(conflict)

with st.expander("Lihat Input Fakta Awal"):
    st.json(answers)

with st.expander("Daftar Rules"):
    for rule in ALL_RULES:
        cond = " AND ".join([f"{k}={v}" for k, v in rule.conditions.items()])
        concl_key, concl_value = rule.conclusion
        st.write(
            f"- {rule.rule_id}: IF {cond} THEN {concl_key}={concl_value} ({rule.description})"
        )