"""REST API de NERIA."""
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from api.engine_adapter import evaluate
from api.errors import (
    DomainValidationError,
    domain_validation_handler,
    request_validation_handler,
)
from api.schemas import (
    ErrorResponse,
    ExpenseEvaluationRequest,
    ExpenseEvaluationResponse,
    HealthResponse,
)
from api.trace import request_id_middleware
REQUEST_ID_HEADER_DOC = {
    "description": (
        "Correlation identifier for this API request."
    ),
    "schema": {
        "type": "string",
    },
}
app = FastAPI(
    title="NERIA API",
    description=(
        "Auditable Expense Intelligence & Compliance API. "
        "Provides decision intelligence without financial authority."
    ),
    version="0.3.0",
)
app.middleware("http")(
    request_id_middleware
)
app.add_exception_handler(
    RequestValidationError,
    request_validation_handler,
)
app.add_exception_handler(
    DomainValidationError,
    domain_validation_handler,
)
@app.get(
    "/health",
    response_model=HealthResponse,
    responses={
        200: {
            "headers": {
                "X-Request-ID":
                    REQUEST_ID_HEADER_DOC,
            }
        }
    },
    tags=["system"],
)
def health() -> HealthResponse:
    """Confirma que el servicio API está disponible."""
    return HealthResponse(
        status="ok",
        service="neria-api",
        phase="4",
    )
@app.post(
    "/v1/expenses/evaluate",
    response_model=ExpenseEvaluationResponse,
    responses={
        200: {
            "headers": {
                "X-Request-ID":
                    REQUEST_ID_HEADER_DOC,
            }
        },
        422: {
            "model": ErrorResponse,
            "description": (
                "Request contract or domain validation error."
            ),
            "headers": {
                "X-Request-ID":
                    REQUEST_ID_HEADER_DOC,
            },
        },
    },
    tags=["expenses"],
)
def evaluate_expense_endpoint(
    request: ExpenseEvaluationRequest,
) -> ExpenseEvaluationResponse:
    """
    Evalúa un gasto mediante el motor determinístico.
    No aprueba pagos ni libera reembolsos.
    """
    try:
        result = evaluate(
            request.model_dump(
                exclude_unset=True
            )
        )
    except (
        KeyError,
        TypeError,
        ValueError,
    ) as error:
        raise DomainValidationError(
            str(error)
        ) from error
    return ExpenseEvaluationResponse(
        **result
    )
