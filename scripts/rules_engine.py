"""Primer tramo del motor determinístico: política corporativa v1.0."""

import re
from datetime import date, datetime
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
MAX_EXPENSE_AGE_DAYS = 30
PROHIBITED_ITEMS = {
    "ALCOHOL",
    "TOBACCO",
    "VAPING",
    "GAMBLING",
    "PERSONAL",
}
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
    """Calcula R01-R10 aplicables sin consultar etiquetas."""
    if "label" in expense or "relationship" in expense:
        raise ValueError("El motor solo acepta datos de entrada")

    if expense["currency"] != "MXN":
        raise ValueError("Esta política v1.0 solo evalúa MXN")

    amount = money(expense["amount_mxn"], "amount_mxn")
    details = expense["input"]
    receipt_state = details["receipt_state"]
    category = expense["category_hint"]
    context = details["category_context"]
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
        attendees = context.get("attendee_count")
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

    if "prohibited_item" in context:
        prohibited_item = context["prohibited_item"]
        if prohibited_item is None:
            normalized_item = "NONE"
        elif isinstance(prohibited_item, str):
            normalized_item = prohibited_item.strip().upper()
        else:
            raise ValueError("prohibited_item debe ser texto o null")

        if normalized_item == "NONE":
            results.append(rule("R03", "PASS", "prohibited_item=NONE"))
        elif normalized_item in PROHIBITED_ITEMS:
            results.append(rule(
                "R03", "VIOLATION",
                f"prohibited_item={normalized_item}",
            ))
        else:
            raise ValueError("prohibited_item no reconocido")

    history = expense.get("history")
    if not isinstance(history, list):
        raise ValueError("history debe ser una lista")
    current_receipt_hash = expense.get("receipt_hash")
    matching_history = 0
    for historical in history:
        if not isinstance(historical, dict):
            raise ValueError(
                "cada elemento de history debe ser un objeto"
            )
        same_identity = (
            historical.get("employee_key")
            == expense.get("employee_key")
            and historical.get("merchant_key")
            == expense.get("merchant_key")
            and historical.get("amount_mxn")
            == expense.get("amount_mxn")
            and historical.get("currency")
            == expense.get("currency")
        )
        same_receipt = (
            current_receipt_hash is not None
            and historical.get("receipt_hash")
            == current_receipt_hash
        )
        if same_identity and same_receipt:
            matching_history += 1
    if matching_history:
        results.append(rule(
            "R04",
            "SIGNAL",
            f"matching_history={matching_history};"
            "receipt_hash_match=true",
        ))
    else:
        results.append(rule(
            "R04", "PASS", "matching_history=0",
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

    submitted_at = details.get("submitted_at")
    expense_date_value = expense.get("expense_date")
    if not isinstance(submitted_at, str):
        raise ValueError("submitted_at debe ser texto ISO 8601")
    if not isinstance(expense_date_value, str):
        raise ValueError("expense_date debe ser texto ISO 8601")

    try:
        submitted_date = datetime.fromisoformat(
            submitted_at.replace("Z", "+00:00")
        ).date()
        expense_date = date.fromisoformat(expense_date_value)
    except ValueError as error:
        raise ValueError("fechas inválidas") from error

    expense_age_days = (submitted_date - expense_date).days
    if expense_age_days < 0:
        raise ValueError("expense_date no puede ser futura")

    age_state = (
        "PASS"
        if expense_age_days <= MAX_EXPENSE_AGE_DAYS
        else "VIOLATION"
    )
    results.append(rule(
        "R06", age_state,
        f"expense_age_days={expense_age_days};"
        f"limit_days={MAX_EXPENSE_AGE_DAYS}",
    ))

    if amount >= HUMAN_REVIEW_THRESHOLD:
        results.append(rule(
            "R07", "CONTROL", "amount_mxn>=10000.00",
        ))

    if category == "AIRFARE":
        travel_class = context.get("travel_class")
        if travel_class is None:
            results.append(rule(
                "R08", "PENDING", "travel_class=MISSING",
            ))
        elif not isinstance(travel_class, str):
            raise ValueError("travel_class debe ser texto")
        else:
            normalized_class = travel_class.strip().upper()
            if not normalized_class:
                raise ValueError(
                    "travel_class no puede estar vacío"
                )
            if normalized_class == "ECONOMY":
                results.append(rule(
                    "R08", "PASS", "travel_class=ECONOMY",
                ))
            else:
                results.append(rule(
                    "R08",
                    "VIOLATION",
                    f"travel_class={normalized_class};"
                    "required=ECONOMY",
                ))
    if category == "MEALS" and "attendee_count" in context:
        attendee_count = context["attendee_count"]
        if attendee_count is None:
            results.append(rule(
                "R09",
                "PENDING",
                "critical_context=attendee_count",
            ))
        elif type(attendee_count) is int and attendee_count >= 1:
            results.append(rule(
                "R09",
                "PASS",
                f"attendee_count={attendee_count}",
            ))
        else:
            raise ValueError(
                "attendee_count debe ser entero positivo o null"
            )
    if "policy_applicable" in context:
        policy_applicable = context["policy_applicable"]
        if policy_applicable is True:
            results.append(rule(
                "R10", "PASS", "policy_applicable=true",
            ))
        elif policy_applicable is None:
            results.append(rule(
                "R10", "PENDING", "policy_applicable=UNKNOWN",
            ))
        elif policy_applicable is False:
            results.append(rule(
                "R10",
                "NOT_APPLICABLE",
                "policy_applicable=false",
            ))
        else:
            raise ValueError(
                "policy_applicable debe ser booleano o null"
            )

    return results
