"""Pruebas de integración del motor determinístico de decisión."""
import json
import sys
import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from decision_engine import evaluate_expense
from load_benchmark import model_input
DECISION_FIELDS = (
    "compliance",
    "risk",
    "route",
    "assessment_complete",
    "permitted_actions",
)
def expected_decision(case):
    label = case["label"]
    return {
        "compliance": label["expected_compliance"],
        "risk": label["expected_risk"],
        "route": label["expected_route"],
        "assessment_complete":
            label["assessment_complete"],
        "permitted_actions":
            label["permitted_actions"],
    }
def actual_decision(case):
    result = evaluate_expense(model_input(case))
    return {
        field: result[field]
        for field in DECISION_FIELDS
    }
class DecisionEngineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.initial_cases = json.loads(
            (
                ROOT
                / "data/generated/"
                "benchmark_development_12_v0_2.json"
            ).read_text(encoding="utf-8")
        )["cases"]
        cls.benchmark_cases = json.loads(
            (
                ROOT
                / "data/generated/"
                "benchmark_300_v0_2.json"
            ).read_text(encoding="utf-8")
        )["cases"]
    def test_initial_12_decisions(self):
        for case in self.initial_cases:
            with self.subTest(case=case["case_ref"]):
                self.assertEqual(
                    actual_decision(case),
                    expected_decision(case),
                )
    def test_all_development_decisions(self):
        checked = 0
        for case in self.benchmark_cases:
            if case["split"] != "DEVELOPMENT":
                continue
            with self.subTest(case=case["case_ref"]):
                self.assertEqual(
                    actual_decision(case),
                    expected_decision(case),
                )
            checked += 1
        self.assertEqual(checked, 180)
    def test_embedded_and_direct_authority_differ(self):
        cases = {
            case["case_ref"]: case
            for case in self.initial_cases
        }
        embedded = evaluate_expense(
            model_input(cases["DEV-010"])
        )
        direct = evaluate_expense(
            model_input(cases["DEV-011"])
        )
        self.assertEqual(
            embedded["route"],
            "SCREENING_COMPLETE",
        )
        self.assertEqual(
            direct["route"],
            "NOT_ADMITTED",
        )
    def test_rejects_expected_label_as_input(self):
        expense = model_input(self.initial_cases[0])
        expense["label"] = self.initial_cases[0]["label"]
        with self.assertRaises(ValueError):
            evaluate_expense(expense)
if __name__ == "__main__":
    unittest.main()
