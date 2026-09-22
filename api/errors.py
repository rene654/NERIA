"""Errores estables y públicos de la API."""
from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from api.trace import get_request_id
class DomainValidationError(Exception):
    """Error esperado producido por el dominio determinístico."""
async def request_validation_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    details = []
    for item in exc.errors():
        details.append(
            {
                "location": list(item["loc"]),
                "message": str(item["msg"]),
                "error_type": str(item["type"]),
            }
        )
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "request_id":
                    get_request_id(request),
                "code":
                    "REQUEST_VALIDATION_ERROR",
                "message": (
                    "The request does not match "
                    "the NERIA API contract."
                ),
                "details": details,
            }
        },
    )
async def domain_validation_handler(
    request: Request,
    exc: DomainValidationError,
) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "request_id":
                    get_request_id(request),
                "code":
                    "DOMAIN_VALIDATION_ERROR",
                "message": (
                    "The expense could not be evaluated "
                    "under the current deterministic policy."
                ),
                "details": [
                    {
                        "location": ["body"],
                        "message": str(exc),
                        "error_type": "domain_error",
                    }
                ],
            }
        },
    )
