"""REST API de NERIA."""
from fastapi import FastAPI, HTTPException
from api.engine_adapter import evaluate
from api.schemas import (
    ExpenseEvaluationRequest,
    ExpenseEvaluationResponse,
    HealthResponse,
)
app = FastAPI(
    title="NERIA API",
    description=(
        "Auditable Expense Intelligence & Compliance API. "
        "Provides decision intelligence without financial authority."
    ),
    version="0.1.0",
)
@app.get(
    "/health",
    response_model=HealthResponse,
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
    tags=["expenses"],
)
def evaluate_expense_endpoint(
    request: ExpenseEvaluationRequest,
) -> ExpenseEvaluationResponse:
    """
    Evalúa un gasto mediante el motor determinístico.
    Este endpoint no aprueba pagos ni libera reembolsos.
    """
    try:
        result = evaluate(
            request.model_dump()
        )
    except (KeyError, TypeError, ValueError) as error:
        raise HTTPException(
            status_code=422,
            detail=str(error),
        ) from error
    return ExpenseEvaluationResponse(
        **result
    )
