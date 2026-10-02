import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from apps.users.models import User


@pytest.mark.django_db
def test_current_user_endpoint_requires_authentication():
    response = APIClient().get(reverse("users:me"))

    assert response.status_code == 403


@pytest.mark.django_db
def test_current_user_endpoint_returns_server_side_role():
    user = User.objects.create_user(
        "clerk",
        "user_123",
        email="client@example.com",
        role=User.Role.CLIENT,
    )
    client = APIClient()
    client.force_authenticate(user=user)

    response = client.get(reverse("users:me"))

    assert response.status_code == 200
    assert response.json() == {
        "id": user.id,
        "email": "client@example.com",
        "phone": "",
        "role": "CLIENT",
        "identity_provider": "clerk",
    }


@pytest.mark.django_db
def test_inactive_user_is_rejected_by_current_user_endpoint():
    user = User.objects.create_user("clerk", "inactive", is_active=False)
    client = APIClient()
    client.force_authenticate(user=user)

    response = client.get(reverse("users:me"))

    assert response.status_code == 403
