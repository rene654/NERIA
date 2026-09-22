"""Contratos públicos de la REST API de NERIA."""
from typing import Any
from pydantic import BaseModel, ConfigDict, Field
class ExpenseInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    submitted_at: str
    receipt_state: str
    receipt_fixture_ref: str | None = None
    receipt_total_mxn: str | None = None
    business_purpose_declared: str | None = None
    category_context: dict[str, Any] = Field(
        default_factory=dict
    )
class ExpenseEvaluationRequest(BaseModel):
    """
    Input permitido para evaluar un gasto.
    No acepta labels, expected outputs ni relaciones
    del benchmark.
    """
    model_config = ConfigDict(extra="forbid")
    organization_profile_key: str
    jurisdiction_country: str
    employee_key: str
    merchant_key: str
    category_hint: str
    amount_mxn: str
    currency: str
    expense_date: str
    receipt_hash: str | None = None
    input: ExpenseInput
    history: list[dict[str, Any]] = Field(
        default_factory=list
    )
class RuleResult(BaseModel):
    rule_code: str
    rule_version: str
    state: str
    evidence_ref: str
class ExpenseEvaluationResponse(BaseModel):
    compliance: str
    risk: str
    route: str
    assessment_complete: bool
    permitted_actions: list[str]
    rules: list[RuleResult]
class HealthResponse(BaseModel):
    status: str
    service: str
    phase: str
