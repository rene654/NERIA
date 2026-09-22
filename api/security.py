"""Minimal server-side authentication and tenant context."""

import json
import os
import secrets
from typing import Literal
from uuid import UUID

from fastapi import Request
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
)
from pydantic import BaseModel, ConfigDict, ValidationError


class AuthContext(BaseModel):
    """Identity established by the server, never by request body."""

    model_config = ConfigDict(extra="forbid")

    organization_id: UUID
    role: Literal[
        "ANALYST",
        "REVIEWER",
        "ADMIN",
    ]


class AuthenticationError(Exception):
    """Credentials are absent or invalid."""


class AuthenticationConfigurationError(Exception):
    """Server-side authentication configuration is invalid."""


bearer_scheme = HTTPBearer(
    auto_error=False,
    scheme_name="NeriaBearerAuth",
    description=(
        "Server-configured Bearer API key. "
        "The credential determines organization and role."
    ),
)


def load_credentials() -> dict[str, AuthContext]:
    """
    Load opaque API keys from server-side configuration.

    Expected format:
    {
      "opaque-api-key": {
        "organization_id": "<uuid>",
        "role": "ANALYST"
      }
    }
    """

    raw = os.environ.get("NERIA_API_KEYS_JSON")

    if not raw:
        raise AuthenticationConfigurationError(
            "NERIA_API_KEYS_JSON is not configured"
        )

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as error:
        raise AuthenticationConfigurationError(
            "NERIA_API_KEYS_JSON is not valid JSON"
        ) from error

    if not isinstance(payload, dict) or not payload:
        raise AuthenticationConfigurationError(
            "NERIA_API_KEYS_JSON must contain credentials"
        )

    credentials: dict[str, AuthContext] = {}

    for token, context in payload.items():
        if (
            not isinstance(token, str)
            or len(token) < 24
        ):
            raise AuthenticationConfigurationError(
                "Configured API keys must be at least 24 characters"
            )

        try:
            credentials[token] = AuthContext.model_validate(
                context
            )
        except ValidationError as error:
            raise AuthenticationConfigurationError(
                "Invalid API key context configuration"
            ) from error

    return credentials


def authenticate_token(token: str) -> AuthContext:
    """Resolve an opaque token to server-controlled tenant context."""

    credentials = load_credentials()

    for configured_token, context in credentials.items():
        if secrets.compare_digest(
            token,
            configured_token,
        ):
            return context

    raise AuthenticationError(
        "Invalid Bearer credential"
    )


def require_auth(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = None,
) -> AuthContext:
    """
    Establish authentication and place tenant context on request.state.
    """

    if credentials is None:
        raise AuthenticationError(
            "Bearer credential is required"
        )

    if credentials.scheme.lower() != "bearer":
        raise AuthenticationError(
            "Bearer credential is required"
        )

    context = authenticate_token(
        credentials.credentials
    )

    request.state.auth_context = context

    return context
