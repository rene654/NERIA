"""Primer tramo del motor determinístico: política corporativa v1.0."""

import re
from decimal import Decimal
from typing import Any


LIMITS_MXN = {
    "HOTEL": Decimal("12000.00"),
    "TRANSPORTATION": Decimal("1000.00"),
    "AIRFARE": Decimal("15000.00"),
    "SOFTWARE": Decimal("3000.00"),
    "OFFICE_SUPPLIES": Decimal("5000.00"),
}

RECEIPT_THRESHOLD = Decimal("500.00")
RECEIPT_TOLERANCE = Decimal("1.00")
HUMAN_REVIEW_THRESHOLD = Decimal("10000.00")
MONEY_PATTERN = re.compile(r"(?:0|[1-9][0-9]*)\.[0-9]{2}\Z")


def money(value: Any, field: str) -> Decimal:
    if not isinstance(value, str) or not MONEY_PATTERN.fullmatch(value):
        raise ValueError(f"{field} debe ser texto con dos decimales")
    return Decimal(value)


def rule(code: str, state: str, evidence: str) -> dict[str, str]:
    return {
        "rule_code": code,
        "rule_version": "v1.0",
        "state": state,
        "evidence_ref": evidence,
    }


def evaluate_core_rules(expense: dict[str, Any]) -> list[dict[str, str]]:
    """Calcula R01, R02, R05 y R07 sin consultar etiquetas."""
    if "label" in expense or "relationship" in expense:
        raise ValueError("El motor solo acepta datos de entrada")

    if expense["currency"] != "MXN":
        raise ValueError("Esta política v1.0 solo evalúa MXN")

    amount = money(expense["amount_mxn"], "amount_mxn")
    details = expense["input"]
    receipt_state = details["receipt_state"]
    category = expense["category_hint"]
    results = []

    if receipt_state == "MISSING":
        if amount > RECEIPT_THRESHOLD:
            state = "VIOLATION"
            evidence = f"amount_mxn={amount:.2f};receipt_state=MISSING"
        else:
            state = "PASS"
            evidence = f"amount_mxn={amount:.2f};receipt_state=OPTIONAL"
        results.append(rule("R01", state, evidence))
    elif receipt_state == "PRESENT_READABLE":
        results.append(rule(
            "R01", "PASS", "receipt_state=PRESENT_READABLE",
        ))
    else:
        results.append(rule(
            "R01", "PENDING", f"receipt_state={receipt_state}",
        ))

    if category == "MEALS":
        attendees = details["category_context"].get("attendee_count")
        if type(attendees) is not int or attendees < 1:
            results.append(rule(
                "R02", "PENDING", "attendee_count=MISSING",
            ))
        else:
            limit = Decimal("600.00") * attendees
            state = "PASS" if amount <= limit else "VIOLATION"
            results.append(rule(
                "R02", state,
                f"amount_mxn={amount:.2f};limit_mxn={limit:.2f}",
            ))
    elif category in LIMITS_MXN:
        limit = LIMITS_MXN[category]
        state = "PASS" if amount <= limit else "VIOLATION"
        results.append(rule(
            "R02", state,
            f"amount_mxn={amount:.2f};limit_mxn={limit:.2f}",
        ))

    if receipt_state == "PRESENT_READABLE":
        receipt_total = details.get("receipt_total_mxn")
        if receipt_total is not None:
            difference = abs(
                amount - money(receipt_total, "receipt_total_mxn")
            )
            state = (
                "PASS" if difference <= RECEIPT_TOLERANCE else "SIGNAL"
            )
            results.append(rule(
                "R05", state,
                f"difference_mxn={difference:.2f};tolerance_mxn=1.00",
            ))

    if amount >= HUMAN_REVIEW_THRESHOLD:
        results.append(rule(
            "R07", "CONTROL", "amount_mxn>=10000.00",
        ))

    return results
