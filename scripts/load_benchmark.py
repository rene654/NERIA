import argparse
import hashlib
import json
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any
def canonical_json(value: Any) -> str:
    """Convierte información a un JSON estable y reproducible."""
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
def calculate_hash(value: Any) -> str:
    """Calcula la huella SHA-256 de la información."""
    content = canonical_json(value).encode("utf-8")
    return hashlib.sha256(content).hexdigest()
def validate_money(value: Any, field_name: str) -> Decimal:
    """Valida que un importe sea numérico y tenga máximo dos decimales."""
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, TypeError) as error:
        raise ValueError(
            f"{field_name} no es un importe válido"
        ) from error
    if amount.as_tuple().exponent < -2:
        raise ValueError(
            f"{field_name} tiene más de dos decimales"
        )
    return amount
def model_input(case: dict[str, Any]) -> dict[str, Any]:
    """
    Devuelve exclusivamente la información que el sistema analizará.
    No incluye label porque contiene la respuesta correcta.
    """
    return {
        "employee_key": case["employee_key"],
        "merchant_key": case["merchant_key"],
        "category_hint": case["category_hint"],
        "amount_mxn": case["amount_mxn"],
        "currency": case["currency"],
        "expense_date": case["expense_date"],
        "receipt_hash": case.get("receipt_hash"),
        "input": case["input"],
        "history": case.get("history", []),
    }
def validate_dataset(
    payload: dict[str, Any],
) -> tuple[list[dict[str, Any]], str]:
    manifest = payload["manifest"]
    cases = payload["cases"]
    if manifest["total_cases"] != len(cases):
        raise ValueError(
            "total_cases no coincide con la cantidad real"
        )
    development_cases = sum(
        case["split"] == "DEVELOPMENT"
        for case in cases
    )
    holdout_cases = sum(
        case["split"] == "HOLDOUT"
        for case in cases
    )
    if manifest["development_cases"] != development_cases:
        raise ValueError(
            "development_cases no coincide con los casos reales"
        )
    if manifest["holdout_cases"] != holdout_cases:
        raise ValueError(
            "holdout_cases no coincide con los casos reales"
        )
    case_ids = [case["case_id"] for case in cases]
    case_refs = [case["case_ref"] for case in cases]
    if len(case_ids) != len(set(case_ids)):
        raise ValueError("Hay case_id duplicados")
    if len(case_refs) != len(set(case_refs)):
        raise ValueError("Hay case_ref duplicados")
    family_splits: dict[str, set[str]] = {}
    prepared_cases = []
    for case in cases:
        family_key = case["family_key"]
        family_splits.setdefault(family_key, set()).add(
            case["split"]
        )
        amount = validate_money(
            case["amount_mxn"],
            f"{case['case_ref']}.amount_mxn",
        )
        if amount <= 0:
            raise ValueError(
                f"{case['case_ref']}.amount_mxn debe ser positivo"
            )
        receipt_total = case["input"].get(
            "receipt_total_mxn"
        )
        if receipt_total is not None:
            validate_money(
                receipt_total,
                f"{case['case_ref']}.receipt_total_mxn",
            )
        prepared_case = dict(case)
        prepared_case["input_hash"] = calculate_hash(
            model_input(case)
        )
        prepared_cases.append(prepared_case)
    leaked_families = [
        family
        for family, splits in family_splits.items()
        if len(splits) > 1
    ]
    if leaked_families:
        raise ValueError(
            "Familias divididas entre DEVELOPMENT y HOLDOUT: "
            + ", ".join(sorted(leaked_families))
        )
    dataset_hash = calculate_hash(payload)
    return prepared_cases, dataset_hash
def main() -> None:
    parser = argparse.ArgumentParser(
        description="Carga reproducible del benchmark NERIA"
    )
    parser.add_argument(
        "fixture",
        type=Path,
        help="Ruta del archivo JSON",
    )
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Valida sin escribir en PostgreSQL",
    )
    args = parser.parse_args()
    payload = json.loads(
        args.fixture.read_text(encoding="utf-8")
    )
    cases, dataset_hash = validate_dataset(payload)
    print(f"Validation: PASS ({len(cases)} cases)")
    print(f"Dataset hash: {dataset_hash}")
    if not args.validate_only:
        raise SystemExit(
            "Database load: NOT IMPLEMENTED. "
            "Por ahora utiliza --validate-only."
        )
if __name__ == "__main__":
    main()