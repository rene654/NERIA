import argparse
import hashlib
import json
import re
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any


CONTRACT_VERSION = "v0.2"
SOURCE_MIGRATION = "007"

MONEY_PATTERN = re.compile(r"^(?:0|[1-9][0-9]*)\.[0-9]{2}$")
COUNTRY_CODE_PATTERN = re.compile(r"^[A-Z]{2}$")
INVALID_JSON_POINTER_ESCAPE = re.compile(r"~(?:[^01]|$)")

ALLOWED_ACTIONS = {
    "RECORD_SCREENING_RESULT",
    "REQUEST_INFORMATION",
    "ROUTE_TO_HUMAN_REVIEW",
    "RETRY_TECHNICAL_PROCESSING",
    "CREATE_TECHNICAL_ALERT",
    "RECORD_NOT_ADMITTED",
}

REQUIRED_ACTIONS_BY_ROUTE = {
    "SCREENING_COMPLETE": {"RECORD_SCREENING_RESULT"},
    "NEEDS_INFORMATION": {"REQUEST_INFORMATION"},
    "HUMAN_REVIEW": {"ROUTE_TO_HUMAN_REVIEW"},
    "SYSTEM_RECOVERY": {
        "RETRY_TECHNICAL_PROCESSING",
        "CREATE_TECHNICAL_ALERT",
    },
    "NOT_ADMITTED": {"RECORD_NOT_ADMITTED"},
}

ALLOWED_VARIANT_TYPES = {
    "BASELINE",
    "REPHRASE",
    "INJECTION",
    "BOUNDARY",
    "MISSING_EVIDENCE",
    "AUTHORITY",
    "COUNTERFACTUAL",
    "DUPLICATE_VARIANT",
    "ADVERSARIAL",
}

ALLOWED_RELATIONSHIP_TYPES = {
    "COUNTERFACTUAL",
    "BOUNDARY_VARIANT",
    "DUPLICATE_VARIANT",
    "ADVERSARIAL",
}

ALLOWED_EXPECTED_EFFECTS = {
    "DECISION_MUST_CHANGE",
    "DECISION_MUST_REMAIN_STABLE",
}

ALLOWED_CHANGED_OUTPUTS = {
    "COMPLIANCE",
    "RISK",
    "ROUTE",
    "RULE_STATES",
    "PERMITTED_ACTIONS",
}

ALLOWED_MISS_SEVERITIES = {
    "LOW",
    "MEDIUM",
    "HIGH",
    "CRITICAL",
}


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


def validate_non_empty_text(value: Any, field_name: str) -> str:
    """Exige texto real, no valores vacíos ni espacios."""
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} debe contener texto")

    return value


def validate_unique_list(value: Any, field_name: str) -> list[Any]:
    """Exige una lista sin elementos duplicados."""
    if not isinstance(value, list):
        raise ValueError(f"{field_name} debe ser una lista")

    fingerprints = [canonical_json(item) for item in value]

    if len(fingerprints) != len(set(fingerprints)):
        raise ValueError(f"{field_name} contiene duplicados")

    return value


def validate_money(value: Any, field_name: str) -> Decimal:
    """Exige un importe serializado como texto con dos decimales."""
    if not isinstance(value, str) or not MONEY_PATTERN.fullmatch(value):
        raise ValueError(
            f"{field_name} debe ser texto con exactamente dos decimales"
        )

    try:
        return Decimal(value)
    except InvalidOperation as error:
        raise ValueError(
            f"{field_name} no es un importe válido"
        ) from error


def validate_json_pointer(pointer: Any, field_name: str) -> str:
    """Valida la sintaxis mínima de un JSON Pointer RFC 6901."""
    validate_non_empty_text(pointer, field_name)

    if not pointer.startswith("/"):
        raise ValueError(f"{field_name} debe iniciar con /")

    if INVALID_JSON_POINTER_ESCAPE.search(pointer):
        raise ValueError(
            f"{field_name} contiene un escape JSON Pointer inválido"
        )

    return pointer


def resolve_json_pointer(document: Any, pointer: str) -> Any:
    """Obtiene el valor señalado por un JSON Pointer validado."""
    current = document

    for raw_token in pointer.split("/")[1:]:
        token = raw_token.replace("~1", "/").replace("~0", "~")

        if isinstance(current, dict):
            if token not in current:
                raise KeyError(pointer)
            current = current[token]
        elif isinstance(current, list):
            if not token.isdigit():
                raise KeyError(pointer)

            index = int(token)

            if index >= len(current):
                raise KeyError(pointer)

            current = current[index]
        else:
            raise KeyError(pointer)

    return current


def model_input(case: dict[str, Any]) -> dict[str, Any]:
    """
    Devuelve exclusivamente la información que el sistema analizará.

    No incluye label ni relationship porque contienen respuestas esperadas.
    """
    return {
        "organization_profile_key": case["organization_profile_key"],
        "jurisdiction_country": case["jurisdiction_country"],
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


def validate_case_metadata(case: dict[str, Any]) -> None:
    """Valida el perfil sintético, la jurisdicción y el tipo de variante."""
    case_ref = case["case_ref"]

    validate_non_empty_text(
        case["organization_profile_key"],
        f"{case_ref}.organization_profile_key",
    )

    country_code = case["jurisdiction_country"]

    if (
        not isinstance(country_code, str)
        or not COUNTRY_CODE_PATTERN.fullmatch(country_code)
    ):
        raise ValueError(
            f"{case_ref}.jurisdiction_country debe usar dos letras mayúsculas"
        )

    if case["variant_type"] not in ALLOWED_VARIANT_TYPES:
        raise ValueError(
            f"{case_ref} contiene variant_type inválido: "
            f"{case['variant_type']}"
        )


def validate_label(case: dict[str, Any]) -> None:
    """Valida severidad, versiones, rutas y límites de autoridad."""
    case_ref = case["case_ref"]
    label = case["label"]
    permitted_actions = validate_unique_list(
        label["permitted_actions"],
        f"{case_ref}.label.permitted_actions",
    )

    if not all(isinstance(action, str) for action in permitted_actions):
        raise ValueError(
            f"{case_ref}.label.permitted_actions solo acepta texto"
        )

    invalid_actions = set(permitted_actions) - ALLOWED_ACTIONS

    if invalid_actions:
        raise ValueError(
            f"{case_ref} contiene acciones inválidas: "
            + ", ".join(sorted(invalid_actions))
        )

    expected_route = label["expected_route"]

    if expected_route not in REQUIRED_ACTIONS_BY_ROUTE:
        raise ValueError(
            f"{case_ref} contiene una ruta inválida: {expected_route}"
        )

    required_actions = REQUIRED_ACTIONS_BY_ROUTE[expected_route]

    if not required_actions.intersection(permitted_actions):
        raise ValueError(
            f"{case_ref} no contiene la acción requerida "
            f"para {expected_route}"
        )

    miss_severity = label["miss_severity"]

    if miss_severity not in ALLOWED_MISS_SEVERITIES:
        raise ValueError(
            f"{case_ref} contiene miss_severity inválida: {miss_severity}"
        )

    validate_non_empty_text(
        label["miss_severity_rationale"],
        f"{case_ref}.label.miss_severity_rationale",
    )

    rules = label["rules"]
    rule_codes = [rule["rule_code"] for rule in rules]

    if len(rule_codes) != len(set(rule_codes)):
        raise ValueError(f"{case_ref} contiene reglas duplicadas")

    for rule in rules:
        validate_non_empty_text(
            rule["rule_version"],
            f"{case_ref}.{rule['rule_code']}.rule_version",
        )


def validate_relationship(
    case: dict[str, Any],
    cases_by_ref: dict[str, dict[str, Any]],
) -> None:
    """Valida una relación contrafactual, de límite o adversarial."""
    relationship = case.get("relationship")

    if relationship is None:
        return

    case_ref = case["case_ref"]

    if not isinstance(relationship, dict):
        raise ValueError(f"{case_ref}.relationship debe ser un objeto")

    relationship_type = relationship["relationship_type"]

    if relationship_type not in ALLOWED_RELATIONSHIP_TYPES:
        raise ValueError(
            f"{case_ref} contiene relationship_type inválido: "
            f"{relationship_type}"
        )

    base_case_ref = relationship["base_case_ref"]

    if base_case_ref == case_ref:
        raise ValueError(f"{case_ref} no puede relacionarse consigo mismo")

    if base_case_ref not in cases_by_ref:
        raise ValueError(
            f"{case_ref} referencia un caso base inexistente: "
            f"{base_case_ref}"
        )

    base_case = cases_by_ref[base_case_ref]

    if base_case["family_key"] != case["family_key"]:
        raise ValueError(
            f"{case_ref} y {base_case_ref} pertenecen a familias distintas"
        )

    if base_case["split"] != case["split"]:
        raise ValueError(
            f"{case_ref} y {base_case_ref} pertenecen a splits distintos"
        )

    changed_fields = validate_unique_list(
        relationship["changed_fields"],
        f"{case_ref}.relationship.changed_fields",
    )

    if not changed_fields:
        raise ValueError(
            f"{case_ref}.relationship.changed_fields no puede estar vacío"
        )

    for index, pointer in enumerate(changed_fields):
        field_name = (
            f"{case_ref}.relationship.changed_fields[{index}]"
        )
        validate_json_pointer(pointer, field_name)

        try:
            base_value = resolve_json_pointer(base_case, pointer)
            variant_value = resolve_json_pointer(case, pointer)
        except KeyError as error:
            raise ValueError(
                f"{field_name} no existe en ambos casos"
            ) from error

        if base_value == variant_value:
            raise ValueError(
                f"{field_name} declara un campo que no cambió"
            )

    expected_effect = relationship["expected_effect"]

    if expected_effect not in ALLOWED_EXPECTED_EFFECTS:
        raise ValueError(
            f"{case_ref} contiene expected_effect inválido: "
            f"{expected_effect}"
        )

    changed_outputs = validate_unique_list(
        relationship["expected_changed_outputs"],
        f"{case_ref}.relationship.expected_changed_outputs",
    )

    if not all(isinstance(output, str) for output in changed_outputs):
        raise ValueError(
            f"{case_ref}.relationship.expected_changed_outputs "
            "solo acepta texto"
        )

    invalid_outputs = set(changed_outputs) - ALLOWED_CHANGED_OUTPUTS

    if invalid_outputs:
        raise ValueError(
            f"{case_ref} contiene outputs inválidos: "
            + ", ".join(sorted(invalid_outputs))
        )

    if (
        expected_effect == "DECISION_MUST_CHANGE"
        and not changed_outputs
    ):
        raise ValueError(
            f"{case_ref} debe declarar qué outputs cambiarán"
        )

    if (
        expected_effect == "DECISION_MUST_REMAIN_STABLE"
        and changed_outputs
    ):
        raise ValueError(
            f"{case_ref} no debe declarar outputs modificados"
        )


def validate_dataset(
    payload: dict[str, Any],
) -> tuple[list[dict[str, Any]], str]:
    manifest = payload["manifest"]
    cases = payload["cases"]

    if manifest["contract_version"] != CONTRACT_VERSION:
        raise ValueError(
            "contract_version debe ser " + CONTRACT_VERSION
        )

    if manifest["source_migration"] != SOURCE_MIGRATION:
        raise ValueError(
            "source_migration debe ser " + SOURCE_MIGRATION
        )

    if manifest["total_cases"] != len(cases):
        raise ValueError(
            "total_cases no coincide con la cantidad real"
        )

    development_cases = sum(
        case["split"] == "DEVELOPMENT" for case in cases
    )
    holdout_cases = sum(
        case["split"] == "HOLDOUT" for case in cases
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

    cases_by_ref = {case["case_ref"]: case for case in cases}
    family_splits: dict[str, set[str]] = {}
    prepared_cases = []

    for case in cases:
        family_key = case["family_key"]
        family_splits.setdefault(family_key, set()).add(case["split"])

        validate_case_metadata(case)

        amount = validate_money(
            case["amount_mxn"],
            f"{case['case_ref']}.amount_mxn",
        )

        if amount <= 0:
            raise ValueError(
                f"{case['case_ref']}.amount_mxn debe ser positivo"
            )

        receipt_total = case["input"].get("receipt_total_mxn")

        if receipt_total is not None:
            validate_money(
                receipt_total,
                f"{case['case_ref']}.receipt_total_mxn",
            )

        validate_label(case)

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

    for case in cases:
        validate_relationship(case, cases_by_ref)

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