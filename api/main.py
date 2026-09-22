"""REST API de NERIA."""

from fastapi import (
    Depends,
    FastAPI,
    Request,
    Security,
)
from fastapi.exceptions import RequestValidationError
from fastapi.security import HTTPAuthorizationCredentials

from api.engine_adapter import evaluate
from api.errors import (
    DomainValidationError,
    authentication_configuration_handler,
    authentication_handler,
    domain_validation_handler,
    request_validation_handler,
)
from api.schemas import (
    ErrorResponse,
    ExpenseEvaluationRequest,
    ExpenseEvaluationResponse,
    HealthResponse,
)
from api.security import (
    AuthContext,
    AuthenticationConfigurationError,
    AuthenticationError,
    bearer_scheme,
    require_auth,
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
    version="0.4.0",
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

app.add_exception_handler(
    AuthenticationError,
    authentication_handler,
)

app.add_exception_handler(
    AuthenticationConfigurationError,
    authentication_configuration_handler,
)


def authenticated_context(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Security(
        bearer_scheme
    ),
) -> AuthContext:
    """Bridge FastAPI security extraction to NERIA auth logic."""

    return require_auth(
        request,
        credentials,
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
    """Public liveness endpoint."""

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
        401: {
            "model": ErrorResponse,
            "description": "Authentication failed.",
            "headers": {
                "X-Request-ID":
                    REQUEST_ID_HEADER_DOC,
            },
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
        503: {
            "model": ErrorResponse,
            "description": (
                "Authentication configuration unavailable."
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
    auth: AuthContext = Depends(
        authenticated_context
    ),
) -> ExpenseEvaluationResponse:
    """
    Evaluate an expense under server-established tenant context.

    Authentication establishes organization identity.
    The request body cannot select its own tenant.

    This endpoint does not approve payments or release reimbursements.
    """

    del auth

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
