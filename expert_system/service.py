from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from .engine import ForwardChainingEngine, InferenceResult
from .rules import ALL_RULES, DIAGNOSIS_DETAILS, GEJALA_MB_WEIGHTS


@dataclass
class CfDetail:
    gejala_id: str
    mb: float
    cf_user: float
    cf_gejala: float


@dataclass
class DiagnosisOutput:
    result: InferenceResult
    diagnosis: str
    diagnosis_detail: str
    cf_value: float
    cf_percent: float
    cf_details: List[CfDetail]


def _compute_cf(initial_facts: Dict[str, str], cf_user: Dict[str, float] | None) -> tuple[float, List[CfDetail]]:
    cf_user = cf_user or {}
    combined = None
    details: List[CfDetail] = []

    for gejala_id, mb in GEJALA_MB_WEIGHTS.items():
        user_cf = float(cf_user.get(gejala_id, 0.0))
        answer = initial_facts.get(gejala_id)
        cf_gejala = mb * user_cf if answer == "YA" else 0.0
        details.append(
            CfDetail(
                gejala_id=gejala_id,
                mb=mb,
                cf_user=user_cf,
                cf_gejala=cf_gejala,
            )
        )

        if cf_gejala > 0:
            combined = cf_gejala if combined is None else combined + cf_gejala * (1 - combined)

    return (combined or 0.0), details


def run_diagnosis(initial_facts: Dict[str, str], cf_user: Dict[str, float] | None = None) -> DiagnosisOutput:
    engine = ForwardChainingEngine(ALL_RULES)
    result = engine.infer(initial_facts)

    diagnosis = result.facts.get("DIAGNOSA", "Tidak dapat ditentukan")
    diagnosis_detail = DIAGNOSIS_DETAILS.get(
        diagnosis,
        "Tidak ada detail rekomendasi karena kombinasi fakta belum tercakup rule.",
    )

    cf_value, cf_details = _compute_cf(initial_facts, cf_user)
    cf_percent = round(cf_value * 100, 1)

    return DiagnosisOutput(
        result=result,
        diagnosis=diagnosis,
        diagnosis_detail=diagnosis_detail,
        cf_value=cf_value,
        cf_percent=cf_percent,
        cf_details=cf_details,
    )
