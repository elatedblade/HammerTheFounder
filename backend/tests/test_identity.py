import pytest
from django.db import IntegrityError, transaction

from apps.users.models import User
from apps.users.services import sync_external_identity


pytestmark = pytest.mark.django_db


def create_external_user(*, provider, subject, email):
    return User.objects.create_user(
        provider,
        subject,
        email=email,
    )


def test_external_identity_sync_is_idempotent():
    first = sync_external_identity(
        "clerk",
        "user_123",
        email="client@example.com",
    )
    second = sync_external_identity(
        "clerk",
        "user_123",
        email="client@example.com",
    )

    assert second.pk == first.pk
    assert User.objects.count() == 1


def test_provider_and_subject_are_unique_together():
    create_external_user(
        provider="clerk",
        subject="user_123",
        email="first@example.com",
    )

    with pytest.raises(IntegrityError):
        with transaction.atomic():
            create_external_user(
                provider="clerk",
                subject="user_123",
                email="second@example.com",
            )


def test_same_subject_can_be_used_by_a_different_provider():
    create_external_user(
        provider="clerk",
        subject="user_123",
        email="clerk@example.com",
    )
    other_provider_user = create_external_user(
        provider="google",
        subject="user_123",
        email="google@example.com",
    )

    assert User.objects.count() == 2
    assert other_provider_user.identity_provider == "google"


def test_external_users_have_unusable_passwords():
    user = create_external_user(
        provider="clerk",
        subject="user_123",
        email="client@example.com",
    )

    assert user.has_usable_password() is False


def test_role_values_include_client_operator_and_admin():
    role_values = set(dict(User._meta.get_field("role").choices))

    assert {User.Role.CLIENT, User.Role.OPERATOR, User.Role.ADMIN} <= role_values
