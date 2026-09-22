"""Errores estables y públicos de la API."""

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from api.security import (
    AuthenticationConfigurationError,
    AuthenticationError,
)
from api.trace import get_request_id


def error_payload(
    request: Request,
    code: str,
    message: str,
    details: list[dict],
) -> dict:
    """Build the stable public error envelope."""

    return {
        "error": {
            "request_id":
                get_request_id(request),
            "code": code,
            "message": message,
            "details": details,
        }
    }


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
        content=error_payload(
            request,
            "REQUEST_VALIDATION_ERROR",
            (
                "The request does not match "
                "the NERIA API contract."
            ),
            details,
        ),
    )


async def domain_validation_handler(
    request: Request,
    exc: DomainValidationError,
) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content=error_payload(
            request,
            "DOMAIN_VALIDATION_ERROR",
            (
                "The expense could not be evaluated "
                "under the current deterministic policy."
            ),
            [
                {
                    "location": ["body"],
                    "message": str(exc),
                    "error_type": "domain_error",
                }
            ],
        ),
    )


async def authentication_handler(
    request: Request,
    exc: AuthenticationError,
) -> JSONResponse:
    return JSONResponse(
        status_code=401,
        headers={
            "WWW-Authenticate": "Bearer",
        },
        content=error_payload(
            request,
            "AUTHENTICATION_REQUIRED",
            "Valid authentication is required.",
            [
                {
                    "location": ["header", "Authorization"],
                    "message": str(exc),
                    "error_type": "authentication_error",
                }
            ],
        ),
    )


async def authentication_configuration_handler(
    request: Request,
    exc: AuthenticationConfigurationError,
) -> JSONResponse:
    del exc

    return JSONResponse(
        status_code=503,
        content=error_payload(
            request,
            "AUTHENTICATION_UNAVAILABLE",
            "Authentication service is not configured.",
            [],
        ),
    )
