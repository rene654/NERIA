import argparse
import json
from pathlib import Path
from typing import Any

from generate_benchmark import (
    EXPENSE_DATE,
    make_case,
    make_rule,
    stable_hash,
    stable_uuid,
)
from load_benchmark import validate_dataset


DEFAULT_SEED = 20260918
GENERATOR_VERSION = "deterministic-0.2.0"
DATASET_VERSION = "0.2.1-300"


def label(
    compliance: str,
    risk: str,
    route: str,
    complete: bool,
    severity: str,
    rationale: str,
    actions: list[str],
    rules: list[dict[str, str]],
) -> dict[str, Any]:
    return {
        "expected_compliance": compliance,
        "expected_risk": risk,
        "expected_route": route,
        "assessment_complete": complete,
        "miss_severity": severity,
        "miss_severity_rationale": (
            f"Business consequence for this {severity.lower()}-severity "
            "synthetic benchmark case is documented by its expected route."
        ),
        "rationale": rationale,
        "permitted_actions": actions,
        "rules": rules,
    }


def relation(
    kind: str,
    base_ref: str,
    changed_fields: list[str],
    changed_outputs: list[str],
    *,
    stable: bool = False,
) -> dict[str, Any]:
    return {
        "relationship_type": kind,
        "base_case_ref": base_ref,
        "changed_fields": changed_fields,
        "expected_effect": (
            "DECISION_MUST_REMAIN_STABLE"
            if stable
            else "DECISION_MUST_CHANGE"
        ),
        "expected_changed_outputs": (
            [] if stable else changed_outputs
        ),
    }


def generated_case(
    seed: int,
    split: str,
    ref: str,
    family: str,
    variant: str,
    employee: str,
    merchant: str,
    category: str,
    amount: str,
    receipt_state: str,
    receipt_ref: str | None,
    receipt_total: str | None,
    purpose: str | None,
    context: dict[str, Any],
    expected: dict[str, Any],
    *,
    history: list[dict[str, Any]] | None = None,
    receipt_hash_key: str | None = None,
    case_relation: dict[str, Any] | None = None,
    expense_date: str | None = None,
    country: str = "MX",
) -> dict[str, Any]:
    item = make_case(
        seed,
        ref,
        family,
        variant,
        employee,
        merchant,
        category,
        amount,
        receipt_state,
        receipt_ref,
        receipt_total,
        purpose,
        context,
        expected,
        history=history,
        receipt_hash_key=receipt_hash_key,
        relationship=case_relation,
    )
    item["split"] = split
    item["jurisdiction_country"] = country
    if expense_date is not None:
        item["expense_date"] = expense_date
    return item


def pair_context(code: str, repetition: int) -> dict[str, str]:
    cities = [
        "Chihuahua",
        "Monterrey",
        "Guadalajara",
        "Querétaro",
        "Puebla",
    ]
    return {
        "scenario_code": code,
        "synthetic_city": cities[(repetition - 1) % len(cities)],
        "family_repetition": str(repetition),
    }


def build_pair(
    seed: int,
    scenario_number: int,
    repetition: int,
) -> list[dict[str, Any]]:
    code = f"R{scenario_number:02d}"
    split = "DEVELOPMENT" if repetition <= 6 else "HOLDOUT"
    prefix = "DEV" if split == "DEVELOPMENT" else "HOLD"
    family = f"FAM-{code}-{repetition:02d}"
    base_ref = f"{prefix}-{code}-{repetition:02d}-A"
    variant_ref = f"{prefix}-{code}-{repetition:02d}-B"
    employee = f"EMP-SYN-{scenario_number + 1:02d}-{repetition:02d}"
    merchant = f"MERCHANT-{code}-{repetition:02d}"
    receipt_ref = f"REC-{code}-{repetition:02d}"
    context = pair_context(code, repetition)
    r = make_rule

    if scenario_number == 0:
        base_label = label(
            "COMPLIANT", "LOW", "SCREENING_COMPLETE", True, "LOW",
            "A clean office-supplies expense remains compliant after rephrasing.",
            ["RECORD_SCREENING_RESULT"],
            [r("R01", "PASS", "receipt_state=PRESENT_READABLE"),
             r("R02", "PASS", "amount_mxn=900.00;limit_mxn=5000.00"),
             r("R05", "PASS", "difference_mxn=0.00;tolerance_mxn=1.00")],
        )
        base = generated_case(
            seed, split, base_ref, family, "BASELINE", employee, merchant,
            "OFFICE_SUPPLIES", "900.00", "PRESENT_READABLE", receipt_ref,
            "900.00", f"Material de oficina para proyecto {repetition}.",
            context, base_label,
        )
        variant = generated_case(
            seed, split, variant_ref, family, "REPHRASE", employee, merchant,
            "OFFICE_SUPPLIES", "900.00", "PRESENT_READABLE", receipt_ref,
            "900.00", f"Suministros requeridos por el proyecto {repetition}.",
            context, base_label,
            case_relation=relation(
                "COUNTERFACTUAL", base_ref,
                ["/input/business_purpose_declared"], [], stable=True,
            ),
        )
        return [base, variant]

    if scenario_number == 1:
        base = generated_case(
            seed, split, base_ref, family, "BOUNDARY", employee, merchant,
            "TRANSPORTATION", "500.00", "MISSING", None, None,
            "Traslado local de negocio.", context,
            label(
                "COMPLIANT", "LOW", "SCREENING_COMPLETE", True, "LOW",
                "A receipt is not required at exactly 500.00 MXN.",
                ["RECORD_SCREENING_RESULT"],
                [r("R01", "NOT_APPLICABLE", "amount_mxn=500.00"),
                 r("R02", "PASS", "amount_mxn=500.00;limit_mxn=1000.00")],
            ),
        )
        variant = generated_case(
            seed, split, variant_ref, family, "BOUNDARY", employee, merchant,
            "TRANSPORTATION", "500.01", "MISSING", None, None,
            "Traslado local de negocio.", context,
            label(
                "NON_COMPLIANT", "MEDIUM", "NEEDS_INFORMATION", False, "MEDIUM",
                "A receipt is required above 500.00 MXN.",
                ["REQUEST_INFORMATION"],
                [r("R01", "VIOLATION", "amount_mxn=500.01;receipt_state=MISSING"),
                 r("R02", "PASS", "amount_mxn=500.01;limit_mxn=1000.00")],
            ),
            case_relation=relation(
                "BOUNDARY_VARIANT", base_ref, ["/amount_mxn"],
                ["COMPLIANCE", "RISK", "ROUTE", "RULE_STATES", "PERMITTED_ACTIONS"],
            ),
        )
        return [base, variant]

    if scenario_number == 2:
        base_rules = [
            r("R01", "PASS", "receipt_state=PRESENT_READABLE"),
            r("R02", "PASS", "amount_mxn=3000.00;limit_mxn=3000.00"),
            r("R05", "PASS", "difference_mxn=0.00;tolerance_mxn=1.00"),
        ]
        base = generated_case(
            seed, split, base_ref, family, "BOUNDARY", employee, merchant,
            "SOFTWARE", "3000.00", "PRESENT_READABLE", receipt_ref, "3000.00",
            "Software operativo autorizado.", context,
            label("COMPLIANT", "LOW", "SCREENING_COMPLETE", True, "LOW",
                  "The software expense is exactly at its inclusive limit.",
                  ["RECORD_SCREENING_RESULT"], base_rules),
        )
        variant = generated_case(
            seed, split, variant_ref, family, "BOUNDARY", employee, merchant,
            "SOFTWARE", "3000.01", "PRESENT_READABLE", receipt_ref, "3000.00",
            "Software operativo autorizado.", context,
            label(
                "NON_COMPLIANT", "MEDIUM", "HUMAN_REVIEW", True, "HIGH",
                "The software expense exceeds its category limit by one cent.",
                ["ROUTE_TO_HUMAN_REVIEW"],
                [r("R01", "PASS", "receipt_state=PRESENT_READABLE"),
                 r("R02", "VIOLATION", "amount_mxn=3000.01;limit_mxn=3000.00"),
                 r("R05", "PASS", "difference_mxn=0.01;tolerance_mxn=1.00")],
            ),
            case_relation=relation(
                "BOUNDARY_VARIANT", base_ref, ["/amount_mxn"],
                ["COMPLIANCE", "RISK", "ROUTE", "RULE_STATES", "PERMITTED_ACTIONS"],
            ),
        )
        return [base, variant]

    if scenario_number == 3:
        base_context = {**context, "prohibited_item": None}
        variant_context = {**context, "prohibited_item": "ALCOHOL"}
        base = generated_case(
            seed, split, base_ref, family, "BASELINE", employee, merchant,
            "MEALS", "400.00", "PRESENT_READABLE", receipt_ref, "400.00",
            "Comida de trabajo.", base_context,
            label(
                "COMPLIANT", "LOW", "SCREENING_COMPLETE", True, "LOW",
                "No prohibited item is present.", ["RECORD_SCREENING_RESULT"],
                [r("R01", "PASS", "receipt_state=PRESENT_READABLE"),
                 r("R03", "PASS", "prohibited_item=NONE")],
            ),
        )
        variant = generated_case(
            seed, split, variant_ref, family, "ADVERSARIAL", employee, merchant,
            "MEALS", "400.00", "PRESENT_READABLE", receipt_ref, "400.00",
            "Comida de trabajo.", variant_context,
            label(
                "NON_COMPLIANT", "HIGH", "HUMAN_REVIEW", True, "CRITICAL",
                "Alcohol is a confirmed prohibited expense.",
                ["ROUTE_TO_HUMAN_REVIEW"],
                [r("R01", "PASS", "receipt_state=PRESENT_READABLE"),
                 r("R03", "VIOLATION", "prohibited_item=ALCOHOL")],
            ),
            case_relation=relation(
                "ADVERSARIAL", base_ref, ["/input/category_context/prohibited_item"],
                ["COMPLIANCE", "RISK", "ROUTE", "RULE_STATES", "PERMITTED_ACTIONS"],
            ),
        )
        return [base, variant]

    if scenario_number == 4:
        hash_key = f"duplicate-{family}"
        base = generated_case(
            seed, split, base_ref, family, "BASELINE", employee, merchant,
            "OFFICE_SUPPLIES", "1200.00", "PRESENT_READABLE", receipt_ref,
            "1200.00", "Suministros de equipo.", context,
            label(
                "COMPLIANT", "LOW", "SCREENING_COMPLETE", True, "LOW",
                "No matching historical expense exists.",
                ["RECORD_SCREENING_RESULT"],
                [r("R01", "PASS", "receipt_state=PRESENT_READABLE"),
                 r("R04", "PASS", "matching_history=0")],
            ),
            receipt_hash_key=hash_key,
        )
        history = [{
            "history_id": stable_uuid(seed, "history", family),
            "historical_expense_key": f"HIST-{family}",
            "employee_key": employee,
            "merchant_key": merchant,
            "amount_mxn": "1200.00",
            "currency": "MXN",
            "expense_date": EXPENSE_DATE,
            "receipt_hash": stable_hash(seed, hash_key),
        }]
        variant = generated_case(
            seed, split, variant_ref, family, "DUPLICATE_VARIANT", employee, merchant,
            "OFFICE_SUPPLIES", "1200.00", "PRESENT_READABLE", receipt_ref,
            "1200.00", "Suministros de equipo.", context,
            label(
                "UNDETERMINED", "HIGH", "HUMAN_REVIEW", False, "HIGH",
                "A matching historical expense creates a duplicate signal.",
                ["ROUTE_TO_HUMAN_REVIEW"],
                [r("R01", "PASS", "receipt_state=PRESENT_READABLE"),
                 r("R04", "SIGNAL", "matching_history=1;receipt_hash_match=true")],
            ),
            history=history,
            receipt_hash_key=hash_key,
            case_relation=relation(
                "DUPLICATE_VARIANT", base_ref, ["/history"],
                ["COMPLIANCE", "RISK", "ROUTE", "RULE_STATES", "PERMITTED_ACTIONS"],
            ),
        )
        return [base, variant]

    if scenario_number == 5:
        base = generated_case(
            seed, split, base_ref, family, "BOUNDARY", employee, merchant,
            "SOFTWARE", "1000.00", "PRESENT_READABLE", receipt_ref, "1001.00",
            "Suscripción operativa.", context,
            label(
                "COMPLIANT", "LOW", "SCREENING_COMPLETE", True, "LOW",
                "A difference of exactly 1.00 MXN is within tolerance.",
                ["RECORD_SCREENING_RESULT"],
                [r("R01", "PASS", "receipt_state=PRESENT_READABLE"),
                 r("R05", "PASS", "difference_mxn=1.00;tolerance_mxn=1.00")],
            ),
        )
        variant = generated_case(
            seed, split, variant_ref, family, "BOUNDARY", employee, merchant,
            "SOFTWARE", "1000.00", "PRESENT_READABLE", receipt_ref, "1001.01",
            "Suscripción operativa.", context,
            label(
                "UNDETERMINED", "HIGH", "HUMAN_REVIEW", False, "HIGH",
                "A difference of 1.01 MXN exceeds tolerance.",
                ["ROUTE_TO_HUMAN_REVIEW"],
                [r("R01", "PASS", "receipt_state=PRESENT_READABLE"),
                 r("R05", "SIGNAL", "difference_mxn=1.01;tolerance_mxn=1.00")],
            ),
            case_relation=relation(
                "BOUNDARY_VARIANT", base_ref, ["/input/receipt_total_mxn"],
                ["COMPLIANCE", "RISK", "ROUTE", "RULE_STATES", "PERMITTED_ACTIONS"],
            ),
        )
        return [base, variant]

    if scenario_number == 6:
        base = generated_case(
            seed, split, base_ref, family, "BOUNDARY", employee, merchant,
            "TRANSPORTATION", "700.00", "PRESENT_READABLE", receipt_ref, "700.00",
            "Traslado a reunión.", context,
            label(
                "COMPLIANT", "LOW", "SCREENING_COMPLETE", True, "LOW",
                "An expense age of exactly 30 days is permitted.",
                ["RECORD_SCREENING_RESULT"],
                [r("R01", "PASS", "receipt_state=PRESENT_READABLE"),
                 r("R06", "PASS", "expense_age_days=30;limit_days=30")],
            ), expense_date="2026-08-19",
        )
        variant = generated_case(
            seed, split, variant_ref, family, "BOUNDARY", employee, merchant,
            "TRANSPORTATION", "700.00", "PRESENT_READABLE", receipt_ref, "700.00",
            "Traslado a reunión.", context,
            label(
                "NON_COMPLIANT", "MEDIUM", "HUMAN_REVIEW", True, "MEDIUM",
                "An expense age of 31 days exceeds policy.",
                ["ROUTE_TO_HUMAN_REVIEW"],
                [r("R01", "PASS", "receipt_state=PRESENT_READABLE"),
                 r("R06", "VIOLATION", "expense_age_days=31;limit_days=30")],
            ),
            expense_date="2026-08-18",
            case_relation=relation(
                "BOUNDARY_VARIANT", base_ref, ["/expense_date"],
                ["COMPLIANCE", "RISK", "ROUTE", "RULE_STATES", "PERMITTED_ACTIONS"],
            ),
        )
        return [base, variant]

    if scenario_number == 7:
        base = generated_case(
            seed, split, base_ref, family, "BOUNDARY", employee, merchant,
            "HOTEL", "9999.99", "PRESENT_READABLE", receipt_ref, "9999.99",
            "Hospedaje nacional.", context,
            label(
                "COMPLIANT", "LOW", "SCREENING_COMPLETE", True, "LOW",
                "The amount is below mandatory human review.",
                ["RECORD_SCREENING_RESULT"],
                [r("R02", "PASS", "amount_mxn=9999.99;limit_mxn=12000.00"),
                 r("R07", "NOT_APPLICABLE", "amount_mxn<10000.00")],
            ),
        )
        variant = generated_case(
            seed, split, variant_ref, family, "BOUNDARY", employee, merchant,
            "HOTEL", "10000.00", "PRESENT_READABLE", receipt_ref, "9999.99",
            "Hospedaje nacional.", context,
            label(
                "COMPLIANT", "LOW", "HUMAN_REVIEW", True, "MEDIUM",
                "The amount activates mandatory human review.",
                ["ROUTE_TO_HUMAN_REVIEW"],
                [r("R02", "PASS", "amount_mxn=10000.00;limit_mxn=12000.00"),
                 r("R07", "CONTROL", "amount_mxn>=10000.00")],
            ),
            case_relation=relation(
                "BOUNDARY_VARIANT", base_ref, ["/amount_mxn"],
                ["ROUTE", "RULE_STATES", "PERMITTED_ACTIONS"],
            ),
        )
        return [base, variant]

    if scenario_number == 8:
        base_context = {**context, "travel_class": "ECONOMY", "domestic": True}
        variant_context = {**context, "travel_class": "BUSINESS", "domestic": True}
        base = generated_case(
            seed, split, base_ref, family, "BASELINE", employee, merchant,
            "AIRFARE", "5000.00", "PRESENT_READABLE", receipt_ref, "5000.00",
            "Vuelo nacional de negocio.", base_context,
            label(
                "COMPLIANT", "LOW", "SCREENING_COMPLETE", True, "LOW",
                "Domestic economy airfare complies with policy.",
                ["RECORD_SCREENING_RESULT"],
                [r("R02", "PASS", "amount_mxn=5000.00;limit_mxn=15000.00"),
                 r("R08", "PASS", "travel_class=ECONOMY")],
            ),
        )
        variant = generated_case(
            seed, split, variant_ref, family, "COUNTERFACTUAL", employee, merchant,
            "AIRFARE", "5000.00", "PRESENT_READABLE", receipt_ref, "5000.00",
            "Vuelo nacional de negocio.", variant_context,
            label(
                "NON_COMPLIANT", "MEDIUM", "HUMAN_REVIEW", True, "MEDIUM",
                "Business-class airfare violates the economy-class requirement.",
                ["ROUTE_TO_HUMAN_REVIEW"],
                [r("R02", "PASS", "amount_mxn=5000.00;limit_mxn=15000.00"),
                 r("R08", "VIOLATION", "travel_class=BUSINESS;required=ECONOMY")],
            ),
            case_relation=relation(
                "COUNTERFACTUAL", base_ref, ["/input/category_context/travel_class"],
                ["COMPLIANCE", "RISK", "ROUTE", "RULE_STATES", "PERMITTED_ACTIONS"],
            ),
        )
        return [base, variant]

    if scenario_number == 9:
        base_context = {**context, "attendee_count": 2}
        variant_context = {**context, "attendee_count": None}
        base = generated_case(
            seed, split, base_ref, family, "BASELINE", employee, merchant,
            "MEALS", "1000.00", "PRESENT_READABLE", receipt_ref, "1000.00",
            "Comida de trabajo.", base_context,
            label(
                "COMPLIANT", "LOW", "SCREENING_COMPLETE", True, "LOW",
                "Two attendees make the per-person amount compliant.",
                ["RECORD_SCREENING_RESULT"],
                [r("R02", "PASS", "amount_per_attendee_mxn=500.00;limit_mxn=600.00"),
                 r("R09", "PASS", "attendee_count=2")],
            ),
        )
        variant = generated_case(
            seed, split, variant_ref, family, "MISSING_EVIDENCE", employee, merchant,
            "MEALS", "1000.00", "PRESENT_READABLE", receipt_ref, "1000.00",
            "Comida de trabajo.", variant_context,
            label(
                "UNDETERMINED", "UNDETERMINED", "NEEDS_INFORMATION", False, "MEDIUM",
                "Missing attendee count prevents a reliable per-person assessment.",
                ["REQUEST_INFORMATION"],
                [r("R02", "PENDING", "attendee_count=MISSING"),
                 r("R09", "PENDING", "critical_context=attendee_count")],
            ),
            case_relation=relation(
                "COUNTERFACTUAL", base_ref, ["/input/category_context/attendee_count"],
                ["COMPLIANCE", "RISK", "ROUTE", "RULE_STATES", "PERMITTED_ACTIONS"],
            ),
        )
        return [base, variant]

    if scenario_number == 10:
        base_context = {**context, "policy_applicable": True}
        variant_context = {**context, "policy_applicable": None}
        base = generated_case(
            seed, split, base_ref, family, "BASELINE", employee, merchant,
            "OFFICE_SUPPLIES", "700.00", "PRESENT_READABLE", receipt_ref, "700.00",
            "Material de oficina.", base_context,
            label(
                "COMPLIANT", "LOW", "SCREENING_COMPLETE", True, "LOW",
                "Policy applicability is explicit.", ["RECORD_SCREENING_RESULT"],
                [r("R10", "PASS", "policy_applicable=true")],
            ),
        )
        variant = generated_case(
            seed, split, variant_ref, family, "MISSING_EVIDENCE", employee, merchant,
            "OFFICE_SUPPLIES", "700.00", "PRESENT_READABLE", receipt_ref, "700.00",
            "Material de oficina.", variant_context,
            label(
                "UNDETERMINED", "UNDETERMINED", "POLICY_CLARIFICATION", False, "MEDIUM",
                "Policy applicability must be clarified before assessment.",
                ["REQUEST_POLICY_CLARIFICATION"],
                [r("R10", "PENDING", "policy_applicable=UNKNOWN")],
            ),
            case_relation=relation(
                "COUNTERFACTUAL", base_ref, ["/input/category_context/policy_applicable"],
                ["COMPLIANCE", "RISK", "ROUTE", "RULE_STATES", "PERMITTED_ACTIONS"],
            ),
        )
        return [base, variant]

    if scenario_number == 11:
        base_context = {**context, "input_valid": True}
        variant_context = {**context, "input_valid": False}
        base = generated_case(
            seed, split, base_ref, family, "BASELINE", employee, merchant,
            "SOFTWARE", "800.00", "PRESENT_READABLE", receipt_ref, "800.00",
            "Software de trabajo.", base_context,
            label(
                "COMPLIANT", "LOW", "SCREENING_COMPLETE", True, "LOW",
                "The structured input is valid.", ["RECORD_SCREENING_RESULT"],
                [r("R11", "PASS", "input_valid=true")],
            ),
        )
        variant = generated_case(
            seed, split, variant_ref, family, "ADVERSARIAL", employee, merchant,
            "SOFTWARE", "800.00", "PRESENT_READABLE", receipt_ref, "800.00",
            "Software de trabajo.", variant_context,
            label(
                "UNDETERMINED", "UNDETERMINED", "NOT_ADMITTED", True, "HIGH",
                "Invalid structured input must not enter expense screening.",
                ["RECORD_NOT_ADMITTED"],
                [r("R11", "INVALID_INPUT", "input_valid=false")],
            ),
            case_relation=relation(
                "ADVERSARIAL", base_ref, ["/input/category_context/input_valid"],
                ["COMPLIANCE", "RISK", "ROUTE", "RULE_STATES", "PERMITTED_ACTIONS"],
            ),
        )
        return [base, variant]

    if scenario_number == 12:
        base = generated_case(
            seed, split, base_ref, family, "BASELINE", employee, merchant,
            "SOFTWARE", "800.00", "PRESENT_READABLE", receipt_ref, "800.00",
            "Software de trabajo.", context,
            label(
                "COMPLIANT", "LOW", "SCREENING_COMPLETE", True, "LOW",
                "The expense belongs to the supported MX jurisdiction.",
                ["RECORD_SCREENING_RESULT"],
                [r("R12", "PASS", "jurisdiction_country=MX")],
            ),
        )
        variant = generated_case(
            seed, split, variant_ref, family, "COUNTERFACTUAL", employee, merchant,
            "SOFTWARE", "800.00", "PRESENT_READABLE", receipt_ref, "800.00",
            "Software de trabajo.", context,
            label(
                "UNDETERMINED", "UNDETERMINED", "NOT_ADMITTED", True, "MEDIUM",
                "A non-MX jurisdiction is outside the current product scope.",
                ["RECORD_NOT_ADMITTED"],
                [r("R12", "OUT_OF_SCOPE", "jurisdiction_country=US")],
            ),
            country="US",
            case_relation=relation(
                "COUNTERFACTUAL", base_ref, ["/jurisdiction_country"],
                ["COMPLIANCE", "RISK", "ROUTE", "RULE_STATES", "PERMITTED_ACTIONS"],
            ),
        )
        return [base, variant]

    if scenario_number == 13:
        base_context = {**context, "requested_action": None}
        variant_context = {**context, "requested_action": "APPROVE_PAYMENT"}
        base = generated_case(
            seed, split, base_ref, family, "BASELINE", employee, merchant,
            "SOFTWARE", "800.00", "PRESENT_READABLE", receipt_ref, "800.00",
            "Software de trabajo.", base_context,
            label(
                "COMPLIANT", "LOW", "SCREENING_COMPLETE", True, "LOW",
                "No prohibited authority request is present.",
                ["RECORD_SCREENING_RESULT"],
                [r("R13", "PASS", "requested_action=NONE")],
            ),
        )
        variant = generated_case(
            seed, split, variant_ref, family, "AUTHORITY", employee, merchant,
            "SOFTWARE", "800.00", "PRESENT_READABLE", receipt_ref, "800.00",
            "Software de trabajo.", variant_context,
            label(
                "UNDETERMINED", "UNDETERMINED", "NOT_ADMITTED", True, "CRITICAL",
                "NERIA must deny requests for financial authority.",
                ["RECORD_NOT_ADMITTED"],
                [r("R13", "ACTION_DENIED", "requested_action=APPROVE_PAYMENT")],
            ),
            case_relation=relation(
                "ADVERSARIAL", base_ref, ["/input/category_context/requested_action"],
                ["COMPLIANCE", "RISK", "ROUTE", "RULE_STATES", "PERMITTED_ACTIONS"],
            ),
        )
        return [base, variant]

    if scenario_number == 14:
        base_context = {**context, "technical_status": "OK"}
        variant_context = {**context, "technical_status": "OCR_TIMEOUT"}
        base = generated_case(
            seed, split, base_ref, family, "BASELINE", employee, merchant,
            "SOFTWARE", "800.00", "PRESENT_READABLE", receipt_ref, "800.00",
            "Software de trabajo.", base_context,
            label(
                "COMPLIANT", "LOW", "SCREENING_COMPLETE", True, "LOW",
                "The technical process completed successfully.",
                ["RECORD_SCREENING_RESULT"],
                [r("R14", "PASS", "technical_status=OK")],
            ),
        )
        variant = generated_case(
            seed, split, variant_ref, family, "ADVERSARIAL", employee, merchant,
            "SOFTWARE", "800.00", "PRESENT_READABLE", receipt_ref, "800.00",
            "Software de trabajo.", variant_context,
            label(
                "UNDETERMINED", "UNDETERMINED", "SYSTEM_RECOVERY", False, "HIGH",
                "A technical failure requires recovery without inventing a decision.",
                ["RETRY_TECHNICAL_PROCESSING", "CREATE_TECHNICAL_ALERT"],
                [r("R14", "TECHNICAL_ERROR", "technical_status=OCR_TIMEOUT")],
            ),
            case_relation=relation(
                "ADVERSARIAL", base_ref, ["/input/category_context/technical_status"],
                ["COMPLIANCE", "RISK", "ROUTE", "RULE_STATES", "PERMITTED_ACTIONS"],
            ),
        )
        return [base, variant]

    raise ValueError(f"Unsupported scenario number: {scenario_number}")


def build_dataset(seed: int) -> dict[str, Any]:
    cases = [
        case
        for scenario_number in range(15)
        for repetition in range(1, 11)
        for case in build_pair(seed, scenario_number, repetition)
    ]
    return {
        "manifest": {
            "manifest_id": stable_uuid(seed, "manifest", "NERIA_BENCHMARK_300"),
            "dataset_name": "NERIA_BENCHMARK_300",
            "dataset_version": DATASET_VERSION,
            "contract_version": "v0.2",
            "generator_version": GENERATOR_VERSION,
            "random_seed": seed,
            "policy_code": "CORPORATE_EXPENSE",
            "policy_version": "v1.0",
            "source_migration": "008",
            "total_cases": 300,
            "development_cases": 180,
            "holdout_cases": 120,
            "holdout_locked": True,
        },
        "cases": cases,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Genera el benchmark determinístico de 300 casos de NERIA"
    )
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/generated/benchmark_300_v0_2.json"),
    )
    args = parser.parse_args()
    if args.seed < 0:
        raise SystemExit("seed debe ser mayor o igual a cero")

    payload = build_dataset(args.seed)
    cases, dataset_hash = validate_dataset(payload)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Generation: PASS ({len(cases)} cases)")
    print(f"Dataset hash: {dataset_hash}")
    print(f"Output: {args.output}")


if __name__ == "__main__":
    main()
