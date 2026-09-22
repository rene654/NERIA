"""Contratos públicos de la REST API de NERIA."""

from datetime import date, datetime
from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)


MONEY_PATTERN = r"^(?:0|[1-9][0-9]*)\.[0-9]{2}$"
COUNTRY_PATTERN = r"^[A-Z]{2}$"
CURRENCY_PATTERN = r"^[A-Z]{3}$"
SHA256_PATTERN = r"^[0-9a-fA-F]{64}$"


class CategoryContext(BaseModel):
    """
    Contexto que el motor determinístico realmente conoce.

    No acepta campos del benchmark como scenario_code,
    family_repetition o expected outputs.
    """

    model_config = ConfigDict(extra="forbid")

    input_valid: bool | None = None
    requested_action: str | None = None
    receipt_text: str | None = None
    technical_status: str | None = None
    attendee_count: int | None = Field(
        default=None,
        ge=1,
    )
    prohibited_item: str | None = None
    travel_class: str | None = None
    policy_applicable: bool | None = None


class ExpenseInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    submitted_at: str
    receipt_state: Literal[
        "MISSING",
        "PRESENT_READABLE",
        "PRESENT_UNREADABLE",
        "UNSUPPORTED",
    ]
    receipt_fixture_ref: str | None = None
    receipt_total_mxn: str | None = Field(
        default=None,
        pattern=MONEY_PATTERN,
    )
    business_purpose_declared: str | None = None
    category_context: CategoryContext = Field(
        default_factory=CategoryContext
    )

    @field_validator("submitted_at")
    @classmethod
    def validate_submitted_at(
        cls,
        value: str,
    ) -> str:
        try:
            parsed = datetime.fromisoformat(
                value.replace("Z", "+00:00")
            )
        except ValueError as error:
            raise ValueError(
                "submitted_at must be ISO 8601"
            ) from error

        if parsed.tzinfo is None:
            raise ValueError(
                "submitted_at must include timezone"
            )

        return value


class HistoricalExpense(BaseModel):
    model_config = ConfigDict(extra="forbid")

    history_id: str | None = None
    historical_expense_key: str | None = None
    employee_key: str = Field(min_length=1)
    merchant_key: str = Field(min_length=1)
    amount_mxn: str = Field(
        pattern=MONEY_PATTERN
    )
    currency: str = Field(
        pattern=CURRENCY_PATTERN
    )
    expense_date: str
    receipt_hash: str | None = Field(
        default=None,
        pattern=SHA256_PATTERN,
    )

    @field_validator("expense_date")
    @classmethod
    def validate_expense_date(
        cls,
        value: str,
    ) -> str:
        try:
            date.fromisoformat(value)
        except ValueError as error:
            raise ValueError(
                "expense_date must be YYYY-MM-DD"
            ) from error

        return value


class ExpenseEvaluationRequest(BaseModel):
    """
    Contrato público para una evaluación de gasto.

    Las respuestas esperadas del benchmark nunca son input.
    """

    model_config = ConfigDict(extra="forbid")

    organization_profile_key: str = Field(
        min_length=1
    )
    jurisdiction_country: str = Field(
        pattern=COUNTRY_PATTERN
    )
    employee_key: str = Field(min_length=1)
    merchant_key: str = Field(min_length=1)

    category_hint: Literal[
        "HOTEL",
        "MEALS",
        "TRANSPORTATION",
        "AIRFARE",
        "SOFTWARE",
        "OFFICE_SUPPLIES",
        "UNKNOWN",
    ]

    amount_mxn: str = Field(
        pattern=MONEY_PATTERN
    )
    currency: str = Field(
        pattern=CURRENCY_PATTERN
    )
    expense_date: str
    receipt_hash: str | None = Field(
        default=None,
        pattern=SHA256_PATTERN,
    )
    input: ExpenseInput
    history: list[HistoricalExpense] = Field(
        default_factory=list
    )

    @field_validator("expense_date")
    @classmethod
    def validate_expense_date(
        cls,
        value: str,
    ) -> str:
        try:
            date.fromisoformat(value)
        except ValueError as error:
            raise ValueError(
                "expense_date must be YYYY-MM-DD"
            ) from error

        return value


class RuleResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rule_code: str
    rule_version: str
    state: str
    evidence_ref: str


class ExpenseEvaluationResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    compliance: str
    risk: str
    route: str
    assessment_complete: bool
    permitted_actions: list[str]
    rules: list[RuleResult]


class HealthResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: str
    service: str
    phase: str


class ErrorDetail(BaseModel):
    location: list[str | int]
    message: str
    error_type: str


class ApiError(BaseModel):
    code: str
    message: str
    details: list[ErrorDetail]


class ErrorResponse(BaseModel):
    error: ApiError
