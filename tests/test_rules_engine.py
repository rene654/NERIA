"""Pruebas del primer tramo contra casos DEVELOPMENT aceptados."""

import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from load_benchmark import model_input
from rules_engine import evaluate_core_rules


class CoreRulesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path = ROOT / "data/generated/benchmark_development_12_v0_2.json"
        cls.cases = json.loads(path.read_text(encoding="utf-8"))["cases"]
        benchmark_path = (
            ROOT / "data/generated/benchmark_300_v0_2.json"
        )
        cls.benchmark_cases = json.loads(
            benchmark_path.read_text(encoding="utf-8")
        )["cases"]

    def test_accepted_development_cases(self):
        selected = {
            "DEV-001", "DEV-002", "DEV-003", "DEV-006", "DEV-007"
        }
        checked = set()

        for case in self.cases:
            if case["case_ref"] not in selected:
                continue

            with self.subTest(case=case["case_ref"]):
                expected = {
                    r["rule_code"]: (
                        r["expected_state"], r["evidence_ref"]
                    )
                    for r in case["label"]["rules"]
                    if r["rule_code"] in {"R01", "R02", "R05", "R07"}
                }
                actual = {
                    r["rule_code"]: (r["state"], r["evidence_ref"])
                    for r in evaluate_core_rules(model_input(case))
                    if r["rule_code"] in expected
                }
                self.assertEqual(actual, expected)
                checked.add(case["case_ref"])

        self.assertEqual(checked, selected)

    def test_prohibited_items_and_expense_age(self):
        checked = 0
        for case in self.benchmark_cases:
            if case["split"] != "DEVELOPMENT":
                continue
            expected = {
                item["rule_code"]: (
                    item["expected_state"],
                    item["evidence_ref"],
                )
                for item in case["label"]["rules"]
                if item["rule_code"] in {"R03", "R06"}
            }
            if not expected:
                continue
            with self.subTest(case=case["case_ref"]):
                actual = {
                    item["rule_code"]: (
                        item["state"],
                        item["evidence_ref"],
                    )
                    for item in evaluate_core_rules(
                        model_input(case)
                    )
                    if item["rule_code"] in expected
                }
                self.assertEqual(actual, expected)
                checked += 1
        self.assertEqual(checked, 24)
    def test_duplicate_airfare_context_and_policy_rules(self):
        expected_codes = {"R04", "R08", "R09", "R10"}
        checked = 0
        for case in self.benchmark_cases:
            if case["split"] != "DEVELOPMENT":
                continue
            expected = {
                item["rule_code"]: (
                    item["expected_state"],
                    item["evidence_ref"],
                )
                for item in case["label"]["rules"]
                if item["rule_code"] in expected_codes
            }
            if not expected:
                continue
            with self.subTest(case=case["case_ref"]):
                actual = {
                    item["rule_code"]: (
                        item["state"],
                        item["evidence_ref"],
                    )
                    for item in evaluate_core_rules(
                        model_input(case)
                    )
                    if item["rule_code"] in expected
                }
                self.assertEqual(actual, expected)
                checked += 1
        self.assertEqual(checked, 48)
    def test_rejects_unknown_item_and_future_date(self):
        expense = copy.deepcopy(model_input(self.cases[0]))
        expense["input"]["category_context"][
            "prohibited_item"
        ] = "UNKNOWN_ITEM"
        with self.assertRaises(ValueError):
            evaluate_core_rules(expense)
        future_expense = copy.deepcopy(model_input(self.cases[0]))
        future_expense["expense_date"] = "2026-09-19"
        with self.assertRaises(ValueError):
            evaluate_core_rules(future_expense)
    def test_receipt_threshold(self):
        for amount, expected in (
            ("500.00", "NOT_APPLICABLE"),
            ("500.01", "VIOLATION"),
        ):
            with self.subTest(amount=amount):
                expense = copy.deepcopy(model_input(self.cases[0]))
                expense["amount_mxn"] = amount
                expense["input"]["receipt_state"] = "MISSING"
                expense["input"]["receipt_fixture_ref"] = None
                expense["input"]["receipt_total_mxn"] = None
                result = evaluate_core_rules(expense)
                self.assertEqual(result[0]["state"], expected)

    def test_rejects_label_and_invalid_money(self):
        expense = model_input(self.cases[0])

        with self.assertRaises(ValueError):
            evaluate_core_rules({**expense, "label": self.cases[0]["label"]})

        with self.assertRaises(ValueError):
            evaluate_core_rules({**expense, "amount_mxn": "2500"})


if __name__ == "__main__":
    unittest.main()
