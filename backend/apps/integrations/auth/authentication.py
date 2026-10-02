from __future__ import annotations

from typing import Any

from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

from apps.users.services import sync_external_identity

from .verifiers import ClerkJWTVerifier, TokenVerifier


class ClerkBearerAuthentication(BaseAuthentication):
    """Authenticate API requests with a verified Clerk bearer token."""

    provider = "clerk"

    def __init__(self, verifier: TokenVerifier | None = None) -> None:
        self.verifier = verifier

    def authenticate(self, request: Any):
        header = request.headers.get("Authorization", "")
        if not header:
            return None
        if not header.startswith("Bearer "):
            raise AuthenticationFailed("Authorization must use the Bearer scheme.")

        token = header.removeprefix("Bearer ").strip()
        if not token:
            raise AuthenticationFailed("Bearer token is missing.")

        try:
            verifier = self.verifier or ClerkJWTVerifier()
            identity = verifier.verify(token)
        except Exception as exc:
            # Do not leak key, issuer, or JWT parsing details to clients.
            raise AuthenticationFailed("Invalid authentication token.") from exc

        user = sync_external_identity(
            identity_provider=self.provider,
            identity_provider_subject=identity.subject,
            email=identity.email,
            phone=identity.phone,
        )
        if not user.is_active:
            raise AuthenticationFailed("This account is inactive.")
        return user, identity

    def authenticate_header(self, request: Any) -> str:
        return 'Bearer realm="htf"'
