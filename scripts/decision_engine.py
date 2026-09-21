"""Agregación determinística de reglas en una decisión auditable."""
from typing import Any
from admission_engine import evaluate_admission
from rules_engine import evaluate_core_rules
def decision(
    compliance: str,
    risk: str,
    route: str,
    assessment_complete: bool,
    permitted_actions: list[str],
    rules: list[dict[str, Any]],
) -> dict[str, Any]:
    """Construye la salida pública del motor."""
    return {
        "compliance": compliance,
        "risk": risk,
        "route": route,
        "assessment_complete": assessment_complete,
        "permitted_actions": permitted_actions,
        "rules": rules,
    }
def aggregate_core_decision(
    rule_results: list[dict[str, Any]],
) -> dict[str, Any]:
    """Convierte resultados R01-R10 en una decisión empresarial."""
    if not isinstance(rule_results, list):
        raise ValueError("rule_results debe ser una lista")
    states: dict[str, str] = {}
    for item in rule_results:
        if not isinstance(item, dict):
            raise ValueError(
                "cada resultado de regla debe ser un objeto"
            )
        code = item.get("rule_code")
        state = item.get("state")
        if not isinstance(code, str) or not code:
            raise ValueError("rule_code inválido")
        if not isinstance(state, str) or not state:
            raise ValueError("state inválido")
        if code in states:
            raise ValueError(
                f"resultado duplicado para {code}"
            )
        states[code] = state
    violations = {
        code
        for code, state in states.items()
        if state == "VIOLATION"
    }
    signals = {
        code
        for code, state in states.items()
        if state == "SIGNAL"
    }
    pending = {
        code
        for code, state in states.items()
        if state == "PENDING"
    }
    controls = {
        code
        for code, state in states.items()
        if state == "CONTROL"
    }
    if violations:
        high_risk = bool(signals) or "R03" in violations
        receipt_only = (
            violations == {"R01"}
            and not signals
            and not pending
            and not controls
        )
        if receipt_only:
            return decision(
                "NON_COMPLIANT",
                "MEDIUM",
                "NEEDS_INFORMATION",
                False,
                ["REQUEST_INFORMATION"],
                rule_results,
            )
        return decision(
            "NON_COMPLIANT",
            "HIGH" if high_risk else "MEDIUM",
            "HUMAN_REVIEW",
            True,
            ["ROUTE_TO_HUMAN_REVIEW"],
            rule_results,
        )
    if signals:
        return decision(
            "UNDETERMINED",
            "HIGH",
            "HUMAN_REVIEW",
            False,
            ["ROUTE_TO_HUMAN_REVIEW"],
            rule_results,
        )
    if pending:
        policy_only = pending == {"R10"}
        return decision(
            "UNDETERMINED",
            "UNDETERMINED",
            (
                "POLICY_CLARIFICATION"
                if policy_only
                else "NEEDS_INFORMATION"
            ),
            False,
            [
                (
                    "REQUEST_POLICY_CLARIFICATION"
                    if policy_only
                    else "REQUEST_INFORMATION"
                )
            ],
            rule_results,
        )
    if controls:
        return decision(
            "COMPLIANT",
            "LOW",
            "HUMAN_REVIEW",
            True,
            ["ROUTE_TO_HUMAN_REVIEW"],
            rule_results,
        )
    return decision(
        "COMPLIANT",
        "LOW",
        "SCREENING_COMPLETE",
        True,
        ["RECORD_SCREENING_RESULT"],
        rule_results,
    )
def evaluate_expense(
    expense: dict[str, Any],
) -> dict[str, Any]:
    """Evalúa admisión, reglas y decisión sin consultar etiquetas."""
    admission = evaluate_admission(expense)
    admission_rules = admission["rules"]
    if not admission["admitted"]:
        return decision(
            "UNDETERMINED",
            "UNDETERMINED",
            admission["route"],
            admission["assessment_complete"],
            admission["permitted_actions"],
            admission_rules,
        )
    core_rules = evaluate_core_rules(expense)
    final = aggregate_core_decision(core_rules)
    final["rules"] = admission_rules + core_rules
    return final
