from __future__ import annotations

import streamlit as st

from expert_system.rules import ALL_RULES, CF_USER_SCALE, GEJALA_QUESTIONS, RIWAYAT_QUESTIONS
from expert_system.service import run_diagnosis


def _escape_label(value: str) -> str:
    return value.replace("\\", "\\\\").replace("\"", "\\\"")


def _join_label_lines(lines: list[str]) -> str:
    if not lines:
        return "-"
    return "\\n".join(_escape_label(line) for line in lines)


def _format_fact_lines(facts: dict[str, str]) -> list[str]:
    return [f"{key}={value}" for key, value in sorted(facts.items())]


def _summarize_derived_facts(facts: dict[str, str]) -> dict[str, str]:
    return {
        "GEJALA": facts.get("GEJALA", "-"),
        "RIWAYAT": facts.get("RIWAYAT", "-"),
        "DIAGNOSA": facts.get("DIAGNOSA", "-"),
    }


def _build_fired_timeline(initial_facts: dict[str, str], output) -> list[dict[str, str]]:
    facts = dict(initial_facts)
    fired_iterations = {
        check.rule_id: check.iteration
        for check in output.result.rule_checks
        if check.status == "FIRED"
    }
    timeline = [
        {
            "step": 0,
            "title": "Fakta Awal",
            "facts": dict(sorted(initial_facts.items())),
            "derived": _summarize_derived_facts(facts),
        }
    ]

    for idx, step in enumerate(output.result.fired_steps, start=1):
        cond = " AND ".join([f"{k}={v}" for k, v in step.conditions.items()])
        concl_key, concl_value = step.conclusion
        facts[concl_key] = concl_value
        timeline.append(
            {
                "step": idx,
                "rule_id": step.rule_id,
                "iteration": fired_iterations.get(step.rule_id),
                "conditions": cond,
                "conclusion": f"{concl_key}={concl_value}",
                "description": step.description,
                "derived": _summarize_derived_facts(facts),
            }
        )

    return timeline


def _build_inference_flowchart(initial_facts: dict[str, str], output) -> str:
    lines = [
        "digraph InferenceFlow {",
        "rankdir=LR;",
        'node [shape=box, style="rounded,filled", fillcolor="#eef6ff", color="#376996", fontname="Helvetica"];',
        'start [label="Fakta Awal"];',
    ]

    fact_lines = _format_fact_lines(initial_facts)
    start_label = _join_label_lines(fact_lines) if fact_lines else "Tidak ada fakta awal"
    lines.append(f'startFacts [label="{start_label}", fillcolor="#f9fcff"];')
    lines.append("start -> startFacts;")

    prev_node = "startFacts"
    for idx, step in enumerate(output.result.fired_steps, start=1):
        cond = _join_label_lines([f"{k}={v}" for k, v in step.conditions.items()])
        concl_key, concl_value = step.conclusion
        rule_node = f"rule{idx}"
        fact_node = f"fact{idx}"

        safe_desc = _escape_label(step.description)
        concl_label = _escape_label(f"{concl_key}={concl_value}")
        lines.append(
            f'{rule_node} [label="{step.rule_id}\\n{safe_desc}", fillcolor="#fff7e6", color="#b7791f"];'
        )
        lines.append(
            f'{fact_node} [label="{concl_label}", fillcolor="#eafbea", color="#2f855a"];'
        )
        lines.append(f'{prev_node} -> {rule_node} [label="{cond}"];')
        lines.append(f"{rule_node} -> {fact_node};")

        prev_node = fact_node

    lines.append(
        f'diagnosis [label="DIAGNOSA={_escape_label(output.diagnosis)}", shape=ellipse, fillcolor="#f3e8ff", color="#6b46c1"];'
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
    st.session_state.setdefault("last_output", None)


def _reset_state() -> None:
    keys_to_remove = [
        key for key in st.session_state.keys() if key.startswith(("ans_", "cf_"))
    ]
    for key in keys_to_remove:
        del st.session_state[key]
    st.session_state["flow_index"] = 0
    st.session_state["answers"] = {}
    st.session_state["cf_user"] = {}
    st.session_state["last_output"] = None
    st.rerun()


st.set_page_config(page_title="Sistem Pakar WiFi", page_icon="📶", layout="wide")
st.markdown(
    """
<style>
@import url("https://fonts.googleapis.com/css2?family=Sora:wght@400;500;600;700&display=swap");
:root {
    --bg-1: #0b1220;
    --bg-2: #0f172a;
    --card: #111827;
    --text: #e2e8f0;
    --muted: #94a3b8;
    --accent: #22d3ee;
    --accent-2: #3b82f6;
    --border: #1f2a44;
}

.stApp {
    background:
        radial-gradient(1200px 600px at 10% -20%, rgba(34, 211, 238, 0.12), transparent 60%),
        radial-gradient(900px 500px at 90% 0%, rgba(59, 130, 246, 0.16), transparent 55%),
        linear-gradient(180deg, var(--bg-1) 0%, var(--bg-2) 100%);
    color: var(--text);
}

.stApp, .stApp * {
    font-family: "Sora", sans-serif;
}

@keyframes fadeUp {
    from {
        opacity: 0;
        transform: translateY(8px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

.hero {
    background: linear-gradient(135deg, rgba(34, 211, 238, 0.12), rgba(59, 130, 246, 0.12));
    border: 1px solid rgba(34, 211, 238, 0.2);
    border-radius: 18px;
    padding: 1.2rem 1.4rem;
    margin-bottom: 1rem;
    animation: fadeUp 320ms ease;
}

.hero-title {
    font-size: 1.6rem;
    font-weight: 700;
    margin-bottom: 0.25rem;
}

.hero-subtitle {
    color: var(--muted);
    font-size: 0.95rem;
    margin-bottom: 0.6rem;
}

.badge {
    display: inline-block;
    padding: 0.2rem 0.6rem;
    border-radius: 999px;
    font-size: 0.75rem;
    font-weight: 600;
    color: #a5f3fc;
    background: rgba(34, 211, 238, 0.12);
    border: 1px solid rgba(34, 211, 238, 0.2);
    margin-right: 0.4rem;
}

.section-title {
    font-size: 1.05rem;
    font-weight: 600;
    letter-spacing: 0.02em;
    margin: 0.4rem 0 0.8rem 0;
    color: var(--text);
}

div[data-testid="stVerticalBlockBorderWrapper"] {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 1rem 1.2rem;
    box-shadow: 0 12px 24px rgba(2, 8, 23, 0.45);
}

div[data-testid="stMetric"] {
    background: #0b1220;
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 0.6rem 0.8rem;
}

.stButton > button {
    border-radius: 10px;
    background: #0b1220;
    border: 1px solid var(--border);
    color: var(--text);
}

.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, var(--accent), var(--accent-2));
    border: none;
    color: #ffffff;
}

.stButton > button:hover {
    border-color: rgba(34, 211, 238, 0.4);
}

div[data-testid="stCaptionContainer"] {
    color: var(--muted);
}

div[data-testid="stExpander"] svg {
    display: none;
}

span[data-testid="stIconMaterial"] {
    display: none;
}
</style>
""",
    unsafe_allow_html=True,
)
st.markdown(
    """
<div class="hero">
    <div class="hero-title">Sistem Pakar Diagnosis WiFi + Internet Rumah</div>
    <div class="hero-subtitle">Inferensi forward chaining berbasis rule set gejala, riwayat, dan target diagnosa.</div>
    <div>
        <span class="badge">Forward Chaining</span>
        <span class="badge">Certainty Factor</span>
    </div>
</div>
""",
    unsafe_allow_html=True,
)

_ensure_state()

total_questions = len(QUESTION_FLOW)
flow_index = st.session_state["flow_index"]
answers: dict[str, str] = st.session_state["answers"]
cf_user: dict[str, float] = st.session_state["cf_user"]

st.markdown('<div class="section-title">Pertanyaan</div>', unsafe_allow_html=True)
progress_value = 1.0 if flow_index >= total_questions else (flow_index + 1) / total_questions
col_progress, col_step, col_answered = st.columns([3, 1, 1])
with col_progress:
    st.progress(progress_value)
with col_step:
    st.metric("Progres", f"{min(flow_index, total_questions)}/{total_questions}")
with col_answered:
    st.metric("Terjawab", f"{len(answers)}/{total_questions}")

if flow_index < total_questions:
    current = QUESTION_FLOW[flow_index]
    question_kind = "Gejala" if current["kind"] == "gejala" else "Riwayat"
    with st.container(border=True):
        st.caption(
            f"Pertanyaan {flow_index + 1} dari {total_questions} | {question_kind} {current['key']}"
        )
        st.markdown(f"**{current['question']}**")

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
            st.session_state["last_output"] = None
            st.session_state["flow_index"] = max(flow_index - 1, 0)
            st.rerun()

        if next_step:
            if current["kind"] == "gejala":
                answers[current["key"]] = answer
                cf_user[current["key"]] = cf_value
            else:
                answers[current["key"]] = mapped_answer
            st.session_state["last_output"] = None
            st.session_state["flow_index"] = flow_index + 1
            st.rerun()
else:
    run_inference = False
    with st.container(border=True):
        st.success("Semua pertanyaan selesai. Silakan jalankan inferensi.")

        col_back, col_reset = st.columns([1, 1])
        with col_back:
            back = st.button("Kembali")
        with col_reset:
            reset = st.button("Reset")

        if reset:
            _reset_state()

        if back:
            st.session_state["last_output"] = None
            st.session_state["flow_index"] = max(flow_index - 1, 0)
            st.rerun()

        run_inference = st.button("Jalankan Inferensi", type="primary")

    if run_inference:
        st.session_state["last_output"] = run_diagnosis(answers, cf_user)

    output = st.session_state.get("last_output")
    if output:
        gejala = output.result.facts.get("GEJALA", "-")
        riwayat = output.result.facts.get("RIWAYAT", "-")

        st.markdown('<div class="section-title">Hasil Diagnosa</div>', unsafe_allow_html=True)
        with st.container(border=True):
            st.success(f"Target Diagnosa: {output.diagnosis}")
            st.info(output.diagnosis_detail)

            col_cf, col_gejala, col_riwayat = st.columns(3)
            with col_cf:
                st.metric("Tingkat Kepercayaan", f"{output.cf_percent:.1f}%")
            with col_gejala:
                st.metric("GEJALA", gejala)
            with col_riwayat:
                st.metric("RIWAYAT", riwayat)

            st.caption("CF(h,e)=MB x CFuser; CFcombine=CF1 + CF2 x (1 - CF1)")

        with st.expander("Detail Certainty Factor"):
            cf_rows = [
                {
                    "Gejala": detail.gejala_id,
                    "Bobot Gejala (MB)": detail.mb,
                    "CF User": detail.cf_user,
                    "CF Gejala": detail.cf_gejala,
                }
                for detail in output.cf_details
            ]
            st.dataframe(cf_rows, use_container_width=True, hide_index=True)

        st.markdown('<div class="section-title">History Forward Chaining (Ringkas)</div>', unsafe_allow_html=True)
        timeline = _build_fired_timeline(answers, output)

        with st.container(border=True):
            st.markdown("**Langkah 0 - Fakta Awal**")
            fact_lines = _format_fact_lines(answers)
            st.text("\n".join(fact_lines) if fact_lines else "-")
            derived = timeline[0]["derived"]
            st.caption(
                "Ringkasan fakta: "
                f"GEJALA={derived['GEJALA']}, "
                f"RIWAYAT={derived['RIWAYAT']}, "
                f"DIAGNOSA={derived['DIAGNOSA']}"
            )

        if output.result.fired_steps:
            for item in timeline[1:]:
                with st.container(border=True):
                    iteration = f" | Iterasi {item['iteration']}" if item.get("iteration") else ""
                    st.markdown(f"**Langkah {item['step']} - {item['rule_id']}{iteration}**")
                    st.markdown(
                        (
                            "<div style='color: var(--muted); font-size: 0.9rem;'>"
                            f"Fakta awal ; Rule {item['rule_id']} ; Fakta baru: {item['conclusion']}"
                            "</div>"
                        ),
                        unsafe_allow_html=True,
                    )
                    st.write(f"Jika: {item['conditions']}")
                    st.write(f"Maka: {item['conclusion']}")
                    st.caption(item["description"])
                    derived = item["derived"]
                    st.write(
                        "Ringkasan fakta: "
                        f"GEJALA={derived['GEJALA']}, "
                        f"RIWAYAT={derived['RIWAYAT']}, "
                        f"DIAGNOSA={derived['DIAGNOSA']}"
                    )
        else:
            st.warning("Tidak ada rule yang terpicu. Periksa rule base atau input.")

        with st.expander("Lihat Alur Inferensi (Graphviz)"):
            st.graphviz_chart(_build_inference_flowchart(answers, output), use_container_width=True)

        st.markdown('<div class="section-title">History Forward Chaining (Lengkap)</div>', unsafe_allow_html=True)
        audit_rows = []
        iter_counters: dict[int, int] = {}
        for check in output.result.rule_checks:
            iter_counters[check.iteration] = iter_counters.get(check.iteration, 0) + 1
            order = iter_counters[check.iteration]
            cond = " AND ".join([f"{k}={v}" for k, v in check.conditions.items()])
            concl_key, concl_value = check.conclusion
            missing = ", ".join(check.missing) if check.missing else "-"
            new_fact = f"{concl_key}={concl_value}" if check.status == "FIRED" else "-"
            audit_rows.append(
                {
                    "Iterasi": check.iteration,
                    "Urutan": order,
                    "Rule": check.rule_id,
                    "Status": STATUS_LABELS.get(check.status, check.status),
                    "Kondisi": cond,
                    "Kesimpulan": f"{concl_key}={concl_value}",
                    "Fakta Baru": new_fact,
                    "Tidak Terpenuhi": missing,
                    "Keterangan": check.description,
                }
            )
        st.dataframe(audit_rows, use_container_width=True, hide_index=True)

        if output.result.conflicts:
            st.markdown('<div class="section-title">Peringatan Konflik</div>', unsafe_allow_html=True)
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