"""Evaluación reproducible y protegida del motor determinístico."""
import argparse
import hashlib
import json
from pathlib import Path
from typing import Any
from decision_engine import evaluate_expense
from load_benchmark import model_input, validate_dataset
ROOT = Path(__file__).resolve().parents[1]
ENGINE_VERSION = "deterministic-rules-v1.0.0"
DECISION_FIELDS = {
    "compliance": "expected_compliance",
    "risk": "expected_risk",
    "route": "expected_route",
    "assessment_complete": "assessment_complete",
    "permitted_actions": "permitted_actions",
}
def engine_hash() -> str:
    """Identifica exactamente el código evaluado."""
    digest = hashlib.sha256()
    for relative_path in (
        "scripts/admission_engine.py",
        "scripts/decision_engine.py",
        "scripts/rules_engine.py",
    ):
        path = ROOT / relative_path
        digest.update(relative_path.encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()
def normalized_value(
    field: str,
    value: Any,
) -> Any:
    """Evita que el orden de acciones afecte la comparación."""
    if field == "permitted_actions":
        return tuple(sorted(value))
    return value
def percentage(
    correct: int,
    total: int,
) -> float:
    if total == 0:
        return 0.0
    return round(correct * 100.0 / total, 6)
def evaluate_split(
    payload: dict[str, Any],
    split: str,
) -> dict[str, Any]:
    """Evalúa un split sin usar etiquetas como entrada."""
    _, dataset_hash = validate_dataset(payload)
    if not isinstance(dataset_hash, str):
        raise RuntimeError(
            "validate_dataset no devolvió el hash canónico"
        )
    cases = [
        case
        for case in payload["cases"]
        if case["split"] == split
    ]
    field_matches = {
        field: 0
        for field in DECISION_FIELDS
    }
    full_decision_matches = 0
    expected_rule_states = 0
    matched_rule_states = 0
    decision_mismatches = []
    rule_mismatches = []
    for case in cases:
        actual = evaluate_expense(model_input(case))
        label = case["label"]
        case_matches = True
        for actual_field, expected_field in (
            DECISION_FIELDS.items()
        ):
            actual_value = normalized_value(
                actual_field,
                actual[actual_field],
            )
            expected_value = normalized_value(
                actual_field,
                label[expected_field],
            )
            if actual_value == expected_value:
                field_matches[actual_field] += 1
            else:
                case_matches = False
                decision_mismatches.append({
                    "case_ref": case["case_ref"],
                    "field": actual_field,
                    "expected": expected_value,
                    "actual": actual_value,
                })
        if case_matches:
            full_decision_matches += 1
        actual_rules = {
            item["rule_code"]: item["state"]
            for item in actual["rules"]
        }
        for expected_rule in label["rules"]:
            code = expected_rule["rule_code"]
            expected_state = expected_rule[
                "expected_state"
            ]
            actual_state = actual_rules.get(code)
            expected_rule_states += 1
            if actual_state == expected_state:
                matched_rule_states += 1
            else:
                rule_mismatches.append({
                    "case_ref": case["case_ref"],
                    "rule_code": code,
                    "expected": expected_state,
                    "actual": actual_state,
                })
    total_cases = len(cases)
    return {
        "dataset_name":
            payload["manifest"]["dataset_name"],
        "dataset_version":
            payload["manifest"]["dataset_version"],
        "dataset_hash": dataset_hash,
        "engine_version": ENGINE_VERSION,
        "engine_hash": engine_hash(),
        "split": split,
        "total_cases": total_cases,
        "full_decision_matches":
            full_decision_matches,
        "full_decision_accuracy": percentage(
            full_decision_matches,
            total_cases,
        ),
        "field_matches": field_matches,
        "field_accuracy": {
            field: percentage(correct, total_cases)
            for field, correct in field_matches.items()
        },
        "expected_rule_states":
            expected_rule_states,
        "matched_rule_states":
            matched_rule_states,
        "rule_state_accuracy": percentage(
            matched_rule_states,
            expected_rule_states,
        ),
        "decision_mismatches":
            decision_mismatches,
        "rule_mismatches":
            rule_mismatches,
    }
def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Evaluate deterministic benchmark decisions "
            "without exposing HOLDOUT by default."
        )
    )
    parser.add_argument(
        "dataset",
        type=Path,
    )
    parser.add_argument(
        "--split",
        choices=("DEVELOPMENT", "HOLDOUT"),
        default="DEVELOPMENT",
    )
    parser.add_argument(
        "--allow-holdout",
        action="store_true",
        help="Explicit authorization required for HOLDOUT.",
    )
    parser.add_argument(
        "--output",
        type=Path,
    )
    args = parser.parse_args()
    if (
        args.split == "HOLDOUT"
        and not args.allow_holdout
    ):
        parser.error(
            "HOLDOUT is locked; use --allow-holdout "
            "only after the engine is frozen"
        )
    payload = json.loads(
        args.dataset.read_text(encoding="utf-8")
    )
    report = evaluate_split(payload, args.split)
    if args.output is not None:
        args.output.parent.mkdir(
            parents=True,
            exist_ok=True,
        )
        args.output.write_text(
            json.dumps(
                report,
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
    print("Evaluation: COMPLETE")
    print("Split:", report["split"])
    print("Cases:", report["total_cases"])
    print(
        "Full decision accuracy:",
        f'{report["full_decision_accuracy"]:.2f}%',
    )
    print(
        "Rule state accuracy:",
        f'{report["rule_state_accuracy"]:.2f}%',
    )
    print(
        "Decision mismatches:",
        len(report["decision_mismatches"]),
    )
    print(
        "Rule mismatches:",
        len(report["rule_mismatches"]),
    )
    print("Dataset hash:", report["dataset_hash"])
    print("Engine hash:", report["engine_hash"])
if __name__ == "__main__":
    main()
