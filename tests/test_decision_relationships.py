"""Pruebas metamórficas de relaciones DEVELOPMENT."""
import json
import sys
import unittest
from collections import Counter
from pathlib import Path
from typing import Any
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from decision_engine import evaluate_expense
from load_benchmark import model_input
OUTPUT_FIELDS = {
    "COMPLIANCE": "compliance",
    "RISK": "risk",
    "ROUTE": "route",
    "PERMITTED_ACTIONS": "permitted_actions",
}
def pointer_value(
    document: dict[str, Any],
    pointer: str,
) -> Any:
    """Resuelve un JSON Pointer simple dentro del input."""
    if not pointer.startswith("/"):
        raise ValueError(
            f"JSON Pointer inválido: {pointer}"
        )
    current: Any = document
    for raw_part in pointer[1:].split("/"):
        part = raw_part.replace("~1", "/").replace("~0", "~")
        if isinstance(current, dict):
            if part not in current:
                raise KeyError(
                    f"{pointer} no existe en el input"
                )
            current = current[part]
        elif isinstance(current, list):
            current = current[int(part)]
        else:
            raise KeyError(
                f"{pointer} atraviesa un valor escalar"
            )
    return current
def rule_states(
    result: dict[str, Any],
) -> tuple[tuple[str, str], ...]:
    """Normaliza reglas para comparar solamente código y estado."""
    return tuple(sorted(
        (
            item["rule_code"],
            item["state"],
        )
        for item in result["rules"]
    ))
def changed_outputs(
    base_result: dict[str, Any],
    variant_result: dict[str, Any],
) -> set[str]:
    """Identifica los resultados empresariales modificados."""
    changed = {
        contract_name
        for contract_name, result_name in OUTPUT_FIELDS.items()
        if base_result[result_name]
        != variant_result[result_name]
    }
    if rule_states(base_result) != rule_states(variant_result):
        changed.add("RULE_STATES")
    return changed
class DecisionRelationshipTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path = (
            ROOT
            / "data/generated/benchmark_300_v0_2.json"
        )
        cls.cases = json.loads(
            path.read_text(encoding="utf-8")
        )["cases"]
        cls.by_reference = {
            case["case_ref"]: case
            for case in cls.cases
        }
    def test_development_relationships(self):
        checked = 0
        relationship_types = Counter()
        for variant in self.cases:
            if variant["split"] != "DEVELOPMENT":
                continue
            relationship = variant.get("relationship")
            if relationship is None:
                continue
            base = self.by_reference[
                relationship["base_case_ref"]
            ]
            with self.subTest(
                variant=variant["case_ref"],
                base=base["case_ref"],
            ):
                self.assertEqual(
                    variant["family_key"],
                    base["family_key"],
                )
                self.assertEqual(
                    variant["split"],
                    base["split"],
                )
                base_input = model_input(base)
                variant_input = model_input(variant)
                self.assertNotIn("label", base_input)
                self.assertNotIn("label", variant_input)
                for pointer in relationship["changed_fields"]:
                    self.assertNotEqual(
                        pointer_value(base_input, pointer),
                        pointer_value(variant_input, pointer),
                        msg=f"{pointer} fue declarado pero no cambió",
                    )
                base_result = evaluate_expense(base_input)
                variant_result = evaluate_expense(
                    variant_input
                )
                actual = changed_outputs(
                    base_result,
                    variant_result,
                )
                expected = set(
                    relationship[
                        "expected_changed_outputs"
                    ]
                )
                if (
                    relationship["expected_effect"]
                    == "DECISION_MUST_CHANGE"
                ):
                    self.assertEqual(actual, expected)
                    self.assertTrue(actual)
                else:
                    self.assertEqual(
                        relationship["expected_effect"],
                        "DECISION_MUST_REMAIN_STABLE",
                    )
                    self.assertEqual(actual, set())
                    self.assertEqual(
                        base_result[
                            "assessment_complete"
                        ],
                        variant_result[
                            "assessment_complete"
                        ],
                    )
            checked += 1
            relationship_types[
                relationship["relationship_type"]
            ] += 1
        self.assertEqual(checked, 90)
        self.assertEqual(
            set(relationship_types),
            {
                "ADVERSARIAL",
                "BOUNDARY_VARIANT",
                "COUNTERFACTUAL",
                "DUPLICATE_VARIANT",
            },
        )
        print(
            "DEVELOPMENT relationships:",
            checked,
        )
        print(
            "Relationship types:",
            dict(sorted(relationship_types.items())),
        )
    def test_holdout_relationship_count_is_not_executed(self):
        holdout_relationships = sum(
            1
            for case in self.cases
            if (
                case["split"] == "HOLDOUT"
                and case.get("relationship") is not None
            )
        )
        self.assertEqual(holdout_relationships, 60)
if __name__ == "__main__":
    unittest.main()
