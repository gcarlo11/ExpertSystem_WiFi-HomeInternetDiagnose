from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple


FactValue = str
Facts = Dict[str, FactValue]


@dataclass(frozen=True)
class Rule:
    rule_id: str
    conditions: Facts
    conclusion: Tuple[str, FactValue]
    description: str


@dataclass
class TraceStep:
    rule_id: str
    description: str
    conditions: Facts
    conclusion: Tuple[str, FactValue]


@dataclass
class RuleCheck:
    iteration: int
    rule_id: str
    description: str
    conditions: Facts
    conclusion: Tuple[str, FactValue]
    met: bool
    status: str
    missing: List[str]


@dataclass
class InferenceResult:
    facts: Facts
    fired_steps: List[TraceStep]
    conflicts: List[str]
    rule_checks: List[RuleCheck]


class ForwardChainingEngine:
    """Simple deterministic forward chaining engine."""

    def __init__(self, rules: List[Rule]) -> None:
        self.rules = rules

    def infer(self, initial_facts: Facts) -> InferenceResult:
        facts = dict(initial_facts)
        fired_rule_ids: set[str] = set()
        fired_steps: List[TraceStep] = []
        conflicts: List[str] = []
        rule_checks: List[RuleCheck] = []

        changed = True
        iteration = 0
        while changed:
            changed = False
            iteration += 1

            for rule in self.rules:
                if rule.rule_id in fired_rule_ids:
                    rule_checks.append(
                        RuleCheck(
                            iteration=iteration,
                            rule_id=rule.rule_id,
                            description=rule.description,
                            conditions=rule.conditions,
                            conclusion=rule.conclusion,
                            met=True,
                            status="ALREADY_FIRED",
                            missing=[],
                        )
                    )
                    continue

                missing = self._missing_conditions(rule.conditions, facts)
                if missing:
                    rule_checks.append(
                        RuleCheck(
                            iteration=iteration,
                            rule_id=rule.rule_id,
                            description=rule.description,
                            conditions=rule.conditions,
                            conclusion=rule.conclusion,
                            met=False,
                            status="NOT_MET",
                            missing=missing,
                        )
                    )
                    continue

                target_fact, target_value = rule.conclusion
                existing_value = facts.get(target_fact)

                if existing_value is not None and existing_value != target_value:
                    rule_checks.append(
                        RuleCheck(
                            iteration=iteration,
                            rule_id=rule.rule_id,
                            description=rule.description,
                            conditions=rule.conditions,
                            conclusion=rule.conclusion,
                            met=True,
                            status="CONFLICT",
                            missing=[],
                        )
                    )
                    conflicts.append(
                        (
                            f"Konflik pada fakta '{target_fact}': "
                            f"nilai lama '{existing_value}', "
                            f"nilai baru '{target_value}' dari rule {rule.rule_id}."
                        )
                    )
                    fired_rule_ids.add(rule.rule_id)
                    continue

                if existing_value == target_value:
                    rule_checks.append(
                        RuleCheck(
                            iteration=iteration,
                            rule_id=rule.rule_id,
                            description=rule.description,
                            conditions=rule.conditions,
                            conclusion=rule.conclusion,
                            met=True,
                            status="ALREADY_TRUE",
                            missing=[],
                        )
                    )
                    fired_rule_ids.add(rule.rule_id)
                    continue

                facts[target_fact] = target_value
                fired_rule_ids.add(rule.rule_id)
                rule_checks.append(
                    RuleCheck(
                        iteration=iteration,
                        rule_id=rule.rule_id,
                        description=rule.description,
                        conditions=rule.conditions,
                        conclusion=rule.conclusion,
                        met=True,
                        status="FIRED",
                        missing=[],
                    )
                )
                fired_steps.append(
                    TraceStep(
                        rule_id=rule.rule_id,
                        description=rule.description,
                        conditions=rule.conditions,
                        conclusion=rule.conclusion,
                    )
                )
                changed = True

        return InferenceResult(
            facts=facts,
            fired_steps=fired_steps,
            conflicts=conflicts,
            rule_checks=rule_checks,
        )

    @staticmethod
    def _conditions_met(conditions: Facts, facts: Facts) -> bool:
        for key, expected in conditions.items():
            if facts.get(key) != expected:
                return False
        return True

    @staticmethod
    def _missing_conditions(conditions: Facts, facts: Facts) -> List[str]:
        missing = []
        for key, expected in conditions.items():
            actual = facts.get(key)
            if actual != expected:
                missing.append(f"{key}={expected} (aktual: {actual or '-'})")
        return missing
