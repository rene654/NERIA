"""Pruebas del evaluador protegido por split."""
import json
import subprocess
import sys
import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from evaluate_benchmark import evaluate_split
class BenchmarkEvaluationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dataset_path = (
            ROOT
            / "data/generated/benchmark_300_v0_2.json"
        )
        cls.payload = json.loads(
            cls.dataset_path.read_text(encoding="utf-8")
        )
    def test_development_reaches_full_accuracy(self):
        report = evaluate_split(
            self.payload,
            "DEVELOPMENT",
        )
        self.assertEqual(report["total_cases"], 180)
        self.assertEqual(
            report["full_decision_matches"],
            180,
        )
        self.assertEqual(
            report["matched_rule_states"],
            report["expected_rule_states"],
        )
        self.assertFalse(
            report["decision_mismatches"]
        )
        self.assertFalse(
            report["rule_mismatches"]
        )
    def test_holdout_requires_explicit_authorization(self):
        completed = subprocess.run(
            [
                sys.executable,
                str(
                    ROOT
                    / "scripts/evaluate_benchmark.py"
                ),
                str(self.dataset_path),
                "--split",
                "HOLDOUT",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn(
            "HOLDOUT is locked",
            completed.stderr,
        )
if __name__ == "__main__":
    unittest.main()
