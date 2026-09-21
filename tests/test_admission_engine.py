# Pruebas del control de admisión R11-R14.

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from admission_engine import evaluate_admission
from load_benchmark import model_input


class AdmissionEngineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.benchmark_300 = json.loads(
            (
                ROOT
                / "data/generated/benchmark_300_v0_2.json"
            ).read_text(encoding="utf-8")
        )["cases"]
        cls.initial_cases = {
            case["case_ref"]: case
            for case in json.loads(
                (
                    ROOT
                    / "data/generated/benchmark_development_12_v0_2.json"
                ).read_text(encoding="utf-8")
            )["cases"]
        }

    def test_development_admission_cases(self):
        codes = {"R11", "R12", "R13", "R14"}
        checked = 0
        blocked = 0

        for case in self.benchmark_300:
            if case["split"] != "DEVELOPMENT":
                continue

            expected = {
                item["rule_code"]: (
                    item["expected_state"],
                    item["evidence_ref"],
                )
                for item in case["label"]["rules"]
                if item["rule_code"] in codes
            }
            if not expected:
                continue

            outcome = evaluate_admission(model_input(case))
            actual = {
                item["rule_code"]: (
                    item["state"],
                    item["evidence_ref"],
                )
                for item in outcome["rules"]
                if item["rule_code"] in expected
            }

            with self.subTest(case=case["case_ref"]):
                self.assertEqual(actual, expected)

                if any(
                    state != "PASS"
                    for state, _ in expected.values()
                ):
                    self.assertEqual(
                        outcome["route"],
                        case["label"]["expected_route"],
                    )
                    self.assertEqual(
                        outcome["assessment_complete"],
                        case["label"]["assessment_complete"],
                    )
                    self.assertEqual(
                        outcome["permitted_actions"],
                        case["label"]["permitted_actions"],
                    )
                    blocked += 1

            checked += 1

        self.assertEqual(checked, 48)
        self.assertEqual(blocked, 24)

    def test_embedded_and_direct_authority_are_distinct(self):
        embedded = evaluate_admission(
            model_input(self.initial_cases["DEV-010"])
        )
        direct = evaluate_admission(
            model_input(self.initial_cases["DEV-011"])
        )

        self.assertTrue(embedded["admitted"])
        self.assertIsNone(embedded["route"])
        self.assertEqual(
            embedded["rules"][-1]["state"],
            "ACTION_DENIED",
        )

        self.assertFalse(direct["admitted"])
        self.assertEqual(direct["route"], "NOT_ADMITTED")
        self.assertEqual(
            direct["permitted_actions"],
            ["RECORD_NOT_ADMITTED"],
        )

    def test_rejects_expected_label_as_input(self):
        case = self.initial_cases["DEV-001"]
        expense = {
            **model_input(case),
            "label": case["label"],
        }

        with self.assertRaises(ValueError):
            evaluate_admission(expense)

    def test_invalid_input_has_first_priority(self):
        expense = model_input(self.initial_cases["DEV-001"])
        expense["jurisdiction_country"] = "US"
        expense["input"]["category_context"] = {
            **expense["input"]["category_context"],
            "input_valid": False,
            "requested_action": "APPROVE_PAYMENT",
            "technical_status": "OCR_TIMEOUT",
        }

        outcome = evaluate_admission(expense)

        self.assertFalse(outcome["admitted"])
        self.assertEqual(outcome["route"], "NOT_ADMITTED")
        self.assertEqual(len(outcome["rules"]), 1)
        self.assertEqual(
            outcome["rules"][0]["rule_code"],
            "R11",
        )
        self.assertEqual(
            outcome["rules"][0]["state"],
            "INVALID_INPUT",
        )


if __name__ == "__main__":
    unittest.main()
