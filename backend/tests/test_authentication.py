from datetime import datetime, timedelta, timezone

import jwt
import pytest
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from django.test import RequestFactory
from django.urls import reverse
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.test import APIClient

from apps.integrations.auth.authentication import ClerkBearerAuthentication
from apps.integrations.auth.verifiers import ClerkJWTVerifier, VerifiedIdentity
from apps.users.models import User


class FakeVerifier:
    def __init__(self, identity=None, error=None):
        self.identity = identity
        self.error = error

    def verify(self, token):
        if self.error:
            raise self.error
        return self.identity


def bearer_request(token=None):
    headers = {}
    if token is not None:
        headers["HTTP_AUTHORIZATION"] = f"Bearer {token}"
    return RequestFactory().get("/", **headers)


def test_missing_bearer_header_is_left_for_permission_classes():
    assert ClerkBearerAuthentication(verifier=FakeVerifier()).authenticate(
        bearer_request()
    ) is None


def test_malformed_bearer_header_is_rejected():
    with pytest.raises(AuthenticationFailed):
        ClerkBearerAuthentication(verifier=FakeVerifier()).authenticate(
            RequestFactory().get("/", HTTP_AUTHORIZATION="Basic token")
        )


def test_invalid_verified_token_is_rejected():
    with pytest.raises(AuthenticationFailed):
        ClerkBearerAuthentication(verifier=FakeVerifier(error=ValueError())).authenticate(
            bearer_request("invalid")
        )


@pytest.mark.django_db
def test_valid_token_syncs_local_identity_and_ignores_claimed_role():
    user, identity = ClerkBearerAuthentication(
        verifier=FakeVerifier(
            identity=VerifiedIdentity(
                subject="clerk_user_123",
                email="client@example.com",
                phone="+15551234567",
            )
        )
    ).authenticate(bearer_request("valid"))

    assert user.identity_provider == "clerk"
    assert user.identity_provider_subject == "clerk_user_123"
    assert user.email == "client@example.com"
    assert user.phone == "+15551234567"
    assert user.role == User.Role.CLIENT
    assert identity.subject == "clerk_user_123"


@pytest.mark.django_db
def test_existing_role_is_preserved_when_token_is_refreshed():
    user = User.objects.create_user(
        "clerk",
        "operator_123",
        email="operator@example.com",
        role=User.Role.OPERATOR,
    )

    authenticated_user, _ = ClerkBearerAuthentication(
        verifier=FakeVerifier(
            identity=VerifiedIdentity(subject="operator_123", email="new@example.com")
        )
    ).authenticate(bearer_request("valid"))

    user.refresh_from_db()
    assert authenticated_user.pk == user.pk
    assert user.role == User.Role.OPERATOR
    assert user.email == "new@example.com"


@pytest.mark.django_db
def test_inactive_local_user_is_rejected_even_with_valid_token():
    User.objects.create_user("clerk", "inactive_123", is_active=False)

    with pytest.raises(AuthenticationFailed):
        ClerkBearerAuthentication(
            verifier=FakeVerifier(identity=VerifiedIdentity(subject="inactive_123"))
        ).authenticate(bearer_request("valid"))


@pytest.mark.django_db
def test_current_user_api_uses_bearer_adapter_and_syncs_identity(monkeypatch):
    identity = VerifiedIdentity(subject="api_user_123", email="api@example.com")
    monkeypatch.setattr(
        "apps.integrations.auth.authentication.ClerkJWTVerifier",
        lambda: FakeVerifier(identity=identity),
    )
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Bearer verified")

    response = client.get(reverse("users:me"))

    assert response.status_code == 200
    assert response.json()["email"] == "api@example.com"
    assert User.objects.filter(
        identity_provider="clerk",
        identity_provider_subject="api_user_123",
    ).exists()


def test_current_user_api_returns_error_envelope_for_invalid_bearer(monkeypatch):
    monkeypatch.setattr(
        "apps.integrations.auth.authentication.ClerkJWTVerifier",
        lambda: FakeVerifier(error=ValueError("bad token")),
    )
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Bearer invalid")

    response = client.get(reverse("users:me"))

    assert response.status_code == 401
    assert response.json() == {
        "code": "UNAUTHENTICATED",
        "message": "Invalid authentication token.",
        "details": {},
    }


@pytest.fixture
def signing_keys():
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_key = private_key.public_key().public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode()
    return private_key, public_key


def make_token(private_key, **overrides):
    claims = {
        "sub": "clerk_user_123",
        "iss": "https://clerk.example.test",
        "aud": "htf",
        "exp": datetime.now(timezone.utc) + timedelta(minutes=5),
    }
    claims.update(overrides)
    return jwt.encode(claims, private_key, algorithm="RS256")


def test_clerk_verifier_validates_signature_issuer_and_audience(signing_keys):
    private_key, public_key = signing_keys
    verifier = ClerkJWTVerifier(
        issuer_url="https://clerk.example.test",
        audience="htf",
        public_key=public_key,
    )

    identity = verifier.verify(make_token(private_key, email="verified@example.com"))

    assert identity == VerifiedIdentity(subject="clerk_user_123", email="verified@example.com")


def test_clerk_verifier_rejects_invalid_signature(signing_keys):
    _, public_key = signing_keys
    other_private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    verifier = ClerkJWTVerifier(
        issuer_url="https://clerk.example.test",
        audience="htf",
        public_key=public_key,
    )

    with pytest.raises(jwt.InvalidTokenError):
        verifier.verify(make_token(other_private_key))


def test_clerk_verifier_rejects_expired_token(signing_keys):
    private_key, public_key = signing_keys
    verifier = ClerkJWTVerifier(
        issuer_url="https://clerk.example.test",
        audience="htf",
        public_key=public_key,
    )

    with pytest.raises(jwt.InvalidTokenError):
        verifier.verify(
            make_token(
                private_key,
                exp=datetime.now(timezone.utc) - timedelta(minutes=1),
            )
        )
