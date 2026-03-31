from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple


FactValue = str
Facts = Dict[str, FactValue]


@dataclass(frozen=True)
class Rule:
    """Represent one IF-THEN rule in the knowledge base."""

    rule_id: str
    conditions: Facts
    conclusion: Tuple[str, FactValue]
    description: str


@dataclass
class TraceStep:
    """Keep one fired rule trace for explainability."""

    rule_id: str
    description: str
    conditions: Facts
    conclusion: Tuple[str, FactValue]


@dataclass
class InferenceResult:
    """Final output of forward chaining process."""

    facts: Facts
    fired_steps: List[TraceStep]
    conflicts: List[str]


class ForwardChainingEngine:
    """Simple deterministic forward chaining engine."""

    def __init__(self, rules: List[Rule]) -> None:
        self.rules = rules

    def infer(self, initial_facts: Facts) -> InferenceResult:
        facts = dict(initial_facts)
        fired_rule_ids: set[str] = set()
        fired_steps: List[TraceStep] = []
        conflicts: List[str] = []

        changed = True
        while changed:
            changed = False

            for rule in self.rules:
                if rule.rule_id in fired_rule_ids:
                    continue

                if not self._conditions_met(rule.conditions, facts):
                    continue

                target_fact, target_value = rule.conclusion
                existing_value = facts.get(target_fact)

                if existing_value is not None and existing_value != target_value:
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
                    fired_rule_ids.add(rule.rule_id)
                    continue

                facts[target_fact] = target_value
                fired_rule_ids.add(rule.rule_id)
                fired_steps.append(
                    TraceStep(
                        rule_id=rule.rule_id,
                        description=rule.description,
                        conditions=rule.conditions,
                        conclusion=rule.conclusion,
                    )
                )
                changed = True

        return InferenceResult(facts=facts, fired_steps=fired_steps, conflicts=conflicts)

    @staticmethod
    def _conditions_met(conditions: Facts, facts: Facts) -> bool:
        for key, expected in conditions.items():
            if facts.get(key) != expected:
                return False
        return True
