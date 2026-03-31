from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

from .engine import ForwardChainingEngine, InferenceResult
from .rules import ALL_RULES, DIAGNOSIS_DETAILS


@dataclass
class DiagnosisOutput:
    result: InferenceResult
    diagnosis: str
    diagnosis_detail: str


def run_diagnosis(initial_facts: Dict[str, str]) -> DiagnosisOutput:
    engine = ForwardChainingEngine(ALL_RULES)
    result = engine.infer(initial_facts)

    diagnosis = result.facts.get("DIAGNOSA", "Tidak dapat ditentukan")
    diagnosis_detail = DIAGNOSIS_DETAILS.get(
        diagnosis,
        "Tidak ada detail rekomendasi karena kombinasi fakta belum tercakup rule.",
    )

    return DiagnosisOutput(result=result, diagnosis=diagnosis, diagnosis_detail=diagnosis_detail)
