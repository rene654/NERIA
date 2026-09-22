"""Request correlation for the NERIA API."""
import re
from collections.abc import Awaitable, Callable
from uuid import uuid4
from fastapi import Request
from starlette.responses import Response
REQUEST_ID_HEADER = "X-Request-ID"
REQUEST_ID_PATTERN = re.compile(
    r"^[A-Za-z0-9._:-]{1,128}$"
)
def valid_request_id(value: str | None) -> bool:
    """Return True only for safe correlation identifiers."""
    if value is None:
        return False
    return bool(
        REQUEST_ID_PATTERN.fullmatch(value)
    )
def get_request_id(request: Request) -> str:
    """Read the correlation ID assigned by middleware."""
    value = getattr(
        request.state,
        "request_id",
        None,
    )
    if isinstance(value, str) and value:
        return value
    return "unavailable"
async def request_id_middleware(
    request: Request,
    call_next: Callable[
        [Request],
        Awaitable[Response],
    ],
) -> Response:
    """
    Attach one request ID to the complete request/response cycle.
    A safe client-provided ID is preserved.
    Missing or malformed IDs are replaced server-side.
    """
    incoming = request.headers.get(
        REQUEST_ID_HEADER
    )
    request_id = (
        incoming
        if valid_request_id(incoming)
        else str(uuid4())
    )
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers[
        REQUEST_ID_HEADER
    ] = request_id
    return response
