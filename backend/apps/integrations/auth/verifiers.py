from __future__ import annotations

import os
from dataclasses import dataclass
from threading import Lock
from typing import Any, Protocol

import jwt
from django.core.exceptions import ImproperlyConfigured
from jwt import InvalidTokenError
from jwt import PyJWKClient


@dataclass(frozen=True)
class VerifiedIdentity:
    """Provider-neutral claims extracted from an already verified token."""

    subject: str
    email: str = ""
    phone: str = ""


class TokenVerifier(Protocol):
    def verify(self, token: str) -> VerifiedIdentity:
        """Verify a bearer token and return trusted identity claims."""


class ClerkJWTVerifier:
    """Verify Clerk-signed JWTs using a configured key or JWKS endpoint."""

    issuer_url: str
    audience: str | None
    public_key: str | None
    jwks_client: PyJWKClient | None

    def __init__(
        self,
        *,
        issuer_url: str | None = None,
        audience: str | None = None,
        public_key: str | None = None,
        jwks_url: str | None = None,
    ) -> None:
        self.issuer_url = issuer_url or os.getenv("CLERK_ISSUER_URL", "").rstrip("/")
        self.audience = audience or os.getenv("CLERK_JWT_AUDIENCE") or None
        configured_key = public_key or os.getenv("CLERK_JWT_PUBLIC_KEY")
        self.public_key = configured_key.replace("\\n", "\n") if configured_key else None
        configured_jwks_url = (
            None
            if self.public_key
            else jwks_url or os.getenv("CLERK_JWKS_URL")
        )
        self.jwks_client = PyJWKClient(configured_jwks_url) if configured_jwks_url else None

        if not self.issuer_url:
            raise ImproperlyConfigured("CLERK_ISSUER_URL must be configured.")
        if not self.public_key and not self.jwks_client:
            raise ImproperlyConfigured(
                "Configure CLERK_JWT_PUBLIC_KEY or CLERK_JWKS_URL for token verification."
            )

    def verify(self, token: str) -> VerifiedIdentity:
        try:
            key: Any = self.public_key
            if self.jwks_client is not None:
                signing_key = self.jwks_client.get_signing_key_from_jwt(token)
                key = signing_key.key

            claims = jwt.decode(
                token,
                key=key,
                algorithms=["RS256"],
                issuer=self.issuer_url,
                audience=self.audience,
                options={"verify_aud": self.audience is not None},
            )
        except (InvalidTokenError, ImproperlyConfigured) as exc:
            raise InvalidTokenError("Invalid Clerk token.") from exc

        subject = claims.get("sub")
        if not isinstance(subject, str) or not subject:
            raise InvalidTokenError("The Clerk token has no subject.")

        return VerifiedIdentity(
            subject=subject,
            email=_claim_string(claims, "email"),
            phone=_claim_string(claims, "phone_number") or _claim_string(claims, "phone"),
        )


_default_verifier: ClerkJWTVerifier | None = None
_default_verifier_factory: object | None = None
_default_verifier_lock = Lock()


def get_clerk_jwt_verifier(*, factory: type[ClerkJWTVerifier] | None = None) -> ClerkJWTVerifier:
    """Return the process-local Clerk verifier, creating it lazily once.

    ``PyJWKClient`` keeps its JWKS cache and refreshes it when a token uses an
    unknown key id, so reusing this verifier preserves normal Clerk key
    rotation behavior without making a network-backed client per request.
    The factory parameter keeps the singleton easy to replace in tests.
    """
    global _default_verifier, _default_verifier_factory

    verifier_factory = factory or ClerkJWTVerifier
    if _default_verifier is None or _default_verifier_factory is not verifier_factory:
        with _default_verifier_lock:
            if _default_verifier is None or _default_verifier_factory is not verifier_factory:
                _default_verifier = verifier_factory()
                _default_verifier_factory = verifier_factory
    return _default_verifier


def reset_clerk_jwt_verifier() -> None:
    """Clear the cached verifier for test isolation or controlled reconfiguration."""
    global _default_verifier, _default_verifier_factory

    with _default_verifier_lock:
        _default_verifier = None
        _default_verifier_factory = None


def _claim_string(claims: dict[str, Any], key: str) -> str:
    value = claims.get(key)
    return value if isinstance(value, str) else ""
