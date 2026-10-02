import pytest
from django.db import IntegrityError, transaction

from apps.users.models import User
from apps.users.services import sync_external_identity


@pytest.mark.django_db
def test_sync_external_identity_is_idempotent_and_updates_profile_data():
    user = sync_external_identity(
        "clerk",
        "user_123",
        email="Founder@Example.com",
        phone="+15551234567",
    )

    same_user = sync_external_identity(
        "clerk",
        "user_123",
        email="updated@example.com",
        phone="+15557654321",
    )

    user.refresh_from_db()
    assert same_user.pk == user.pk
    assert User.objects.count() == 1
    assert user.email == "updated@example.com"
    assert user.phone == "+15557654321"
    assert user.role == User.Role.CLIENT
    assert not user.has_usable_password()


@pytest.mark.django_db
def test_external_identity_pair_is_unique():
    User.objects.create_user("clerk", "user_123")

    with pytest.raises(IntegrityError):
        with transaction.atomic():
            User.objects.create_user("clerk", "user_123")

    User.objects.create_user("other-provider", "user_123")
