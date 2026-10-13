import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from apps.audit.models import AuditEntry
from apps.events.models import Event
from apps.users.models import User


@pytest.mark.django_db
def test_current_user_endpoint_requires_authentication():
    response = APIClient().get(reverse("users:me"))

    assert response.status_code == 401
    assert response.json() == {
        "code": "UNAUTHENTICATED",
        "message": "Authentication credentials were not provided.",
        "details": {},
    }


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


def make_user(subject, *, role=User.Role.CLIENT, active=True, provider="clerk"):
    return User.objects.create_user(
        provider,
        subject,
        email=f"{subject}@example.com",
        role=role,
        is_active=active,
    )


@pytest.mark.django_db
def test_user_management_is_superadmin_only():
    admin = make_user("admin", role=User.Role.ADMIN)
    target = make_user("target")
    client = APIClient()
    client.force_authenticate(user=admin)

    list_response = client.get(reverse("users:admin-users"))
    role_response = client.patch(
        reverse("users:admin-user-role", kwargs={"user_id": target.id}),
        {"role": User.Role.OPERATOR},
        format="json",
    )

    assert list_response.status_code == 403
    assert role_response.status_code == 403


@pytest.mark.django_db
def test_superadmin_can_list_active_clerk_users():
    superadmin = make_user("superadmin", role=User.Role.SUPERADMIN)
    active = make_user("active", role=User.Role.OPERATOR)
    make_user("inactive", active=False)
    make_user("other-provider", provider="google")
    client = APIClient()
    client.force_authenticate(user=superadmin)

    response = client.get(reverse("users:admin-users"))

    assert response.status_code == 200
    assert response.json() == [
        {
            "id": active.id,
            "email": "active@example.com",
            "clerk_subject": "active",
            "role": "OPERATOR",
            "status": "ACTIVE",
        },
        {
            "id": superadmin.id,
            "email": "superadmin@example.com",
            "clerk_subject": "superadmin",
            "role": "SUPERADMIN",
            "status": "ACTIVE",
        },
    ]


@pytest.mark.django_db
def test_superadmin_can_change_role_and_change_is_audited():
    superadmin = make_user("superadmin", role=User.Role.SUPERADMIN)
    target = make_user("target")
    client = APIClient()
    client.force_authenticate(user=superadmin)

    response = client.patch(
        reverse("users:admin-user-role", kwargs={"user_id": target.id}),
        {"role": User.Role.ADMIN},
        format="json",
    )

    assert response.status_code == 200
    assert response.json()["role"] == User.Role.ADMIN
    target.refresh_from_db()
    assert target.role == User.Role.ADMIN
    event = Event.objects.get(event_type="user.role_changed")
    assert event.actor_id == superadmin.id
    assert event.payload == {
        "user_id": target.id,
        "from": User.Role.CLIENT,
        "to": User.Role.ADMIN,
    }
    assert AuditEntry.objects.get(event=event).action == "user.role_changed"


@pytest.mark.django_db
def test_superadmin_cannot_remove_the_last_active_superadmin():
    superadmin = make_user("superadmin", role=User.Role.SUPERADMIN)
    client = APIClient()
    client.force_authenticate(user=superadmin)

    response = client.patch(
        reverse("users:admin-user-role", kwargs={"user_id": superadmin.id}),
        {"role": User.Role.ADMIN},
        format="json",
    )

    assert response.status_code == 409
    assert response.json()["code"] == "LAST_SUPERADMIN"
    superadmin.refresh_from_db()
    assert superadmin.role == User.Role.SUPERADMIN
