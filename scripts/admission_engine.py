# Control de admisión determinístico para la política v1.0.

from typing import Any

from rules_engine import rule


PROHIBITED_ACTIONS = {
    "APPROVE_PAYMENT",
    "RELEASE_REIMBURSEMENT",
}


def result(
    admitted: bool,
    route: str | None,
    assessment_complete: bool | None,
    permitted_actions: list[str],
    rules: list[dict[str, str]],
) -> dict[str, Any]:
    return {
        "admitted": admitted,
        "route": route,
        "assessment_complete": assessment_complete,
        "permitted_actions": permitted_actions,
        "rules": rules,
    }


def evaluate_admission(expense: dict[str, Any]) -> dict[str, Any]:
    if "label" in expense or "relationship" in expense:
        raise ValueError("El motor solo acepta datos de entrada")

    context = expense["input"]["category_context"]
    rules: list[dict[str, str]] = []

    if "input_valid" in context:
        if context["input_valid"] is not True:
            rules.append(rule(
                "R11", "INVALID_INPUT", "input_valid=false",
            ))
            return result(
                False,
                "NOT_ADMITTED",
                True,
                ["RECORD_NOT_ADMITTED"],
                rules,
            )
        rules.append(rule("R11", "PASS", "input_valid=true"))

    country = expense["jurisdiction_country"]
    if country != "MX":
        rules.append(rule(
            "R12", "OUT_OF_SCOPE",
            f"jurisdiction_country={country}",
        ))
        return result(
            False,
            "NOT_ADMITTED",
            True,
            ["RECORD_NOT_ADMITTED"],
            rules,
        )
    rules.append(rule("R12", "PASS", "jurisdiction_country=MX"))

    requested = context.get("requested_action")
    requested_code = (
        str(requested).strip().upper()
        if requested is not None
        else None
    )

    if requested_code in PROHIBITED_ACTIONS:
        rules.append(rule(
            "R13", "ACTION_DENIED",
            f"requested_action={requested_code}",
        ))
        return result(
            False,
            "NOT_ADMITTED",
            True,
            ["RECORD_NOT_ADMITTED"],
            rules,
        )

    receipt_text = str(context.get("receipt_text") or "").upper()
    embedded_approval = (
        "APPROVE_PAYMENT" in receipt_text
        or "APPROVE PAYMENT" in receipt_text
    )

    if embedded_approval:
        rules.append(rule(
            "R13", "ACTION_DENIED",
            "embedded_action=APPROVE_PAYMENT",
        ))
    elif "requested_action" in context:
        rules.append(rule(
            "R13", "PASS", "requested_action=NONE",
        ))

    if "technical_status" in context:
        technical_status = str(context["technical_status"]).upper()
        if technical_status != "OK":
            rules.append(rule(
                "R14", "TECHNICAL_ERROR",
                f"technical_status={technical_status}",
            ))
            return result(
                False,
                "SYSTEM_RECOVERY",
                False,
                [
                    "RETRY_TECHNICAL_PROCESSING",
                    "CREATE_TECHNICAL_ALERT",
                ],
                rules,
            )
        rules.append(rule(
            "R14", "PASS", "technical_status=OK",
        ))

    return result(True, None, None, [], rules)
