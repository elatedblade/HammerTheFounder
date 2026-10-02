import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from apps.candidates.models import CandidateProfile
from apps.users.models import User


pytestmark = pytest.mark.django_db


def make_user(*, role=User.Role.CLIENT, active=True, subject="candidate"):
    return User.objects.create_user(
        "clerk",
        subject,
        email=f"{subject}@example.com",
        role=role,
        is_active=active,
    )


def client_for(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


def profile_payload(version=0, **overrides):
    payload = {
        "profile_version": version,
        "full_name": "Ada Lovelace",
        "headline": "Staff engineer",
        "location": "London",
        "experience_summary": "Builds reliable systems.",
        "target_roles": ["Staff Engineer"],
        "preferred_locations": ["London"],
        "remote_preference": "HYBRID",
    }
    payload.update(overrides)
    return payload


def test_get_missing_profile_is_null_and_has_no_side_effect():
    user = make_user()
    response = client_for(user).get(reverse("candidates:profile"))

    assert response.status_code == 200
    assert response.json() is None
    assert CandidateProfile.objects.count() == 0


def test_create_reopen_and_patch_profile():
    user = make_user()
    client = client_for(user)
    url = reverse("candidates:profile")

    created = client.patch(url, profile_payload(), format="json")
    assert created.status_code == 200
    assert created.json()["profile_version"] == 1
    assert created.json()["basics_complete"] is True

    reopened = client.get(url)
    assert reopened.status_code == 200
    assert reopened.json()["id"] == created.json()["id"]

    updated = client.patch(
        url,
        {"profile_version": 1, "headline": "Principal engineer"},
        format="json",
    )
    assert updated.status_code == 200
    assert updated.json()["headline"] == "Principal engineer"
    assert updated.json()["profile_version"] == 2


def test_two_clients_are_isolated():
    first, second = make_user(subject="first"), make_user(subject="second")
    first_client, second_client = client_for(first), client_for(second)
    url = reverse("candidates:profile")

    first_client.patch(url, profile_payload(), format="json")
    response = second_client.patch(
        url,
        profile_payload(full_name="Grace Hopper"),
        format="json",
    )

    assert response.status_code == 200
    assert response.json()["full_name"] == "Grace Hopper"
    assert CandidateProfile.objects.get(user=first).full_name == "Ada Lovelace"
    assert CandidateProfile.objects.get(user=second).full_name == "Grace Hopper"


@pytest.mark.parametrize("field", ["id", "owner", "user", "status"])
def test_client_cannot_inject_ownership_or_immutable_fields(field):
    user = make_user()
    payload = profile_payload(**{field: 123})

    response = client_for(user).patch(
        reverse("candidates:profile"), payload, format="json"
    )

    assert response.status_code == 400
    assert field in response.json()["details"]
    assert CandidateProfile.objects.count() == 0


def test_unknown_field_is_rejected():
    user = make_user()
    response = client_for(user).patch(
        reverse("candidates:profile"),
        profile_payload(unknown="value"),
        format="json",
    )

    assert response.status_code == 400
    assert "unknown" in response.json()["details"]


def test_missing_version_and_invalid_profile_values_are_rejected():
    user = make_user()
    url = reverse("candidates:profile")
    missing_version = profile_payload()
    del missing_version["profile_version"]

    response = client_for(user).patch(url, missing_version, format="json")
    assert response.status_code == 400
    assert "profile_version" in response.json()["details"]

    invalid = client_for(user).patch(
        url,
        profile_payload(target_roles=[" Engineer ", "Engineer"]),
        format="json",
    )
    assert invalid.status_code == 400
    assert CandidateProfile.objects.count() == 0


def test_stale_version_returns_conflict_envelope():
    user = make_user()
    client = client_for(user)
    url = reverse("candidates:profile")
    client.patch(url, profile_payload(), format="json")

    response = client.patch(
        url,
        {"profile_version": 0, "headline": "Stale"},
        format="json",
    )

    assert response.status_code == 409
    assert response.json()["code"] == "STALE_PROFILE_VERSION"
    assert response.json()["details"] == {}


def test_first_create_requires_zero_version_and_duplicate_create_is_rejected():
    user = make_user()
    client = client_for(user)
    url = reverse("candidates:profile")

    wrong_first_version = client.patch(
        url, profile_payload(version=1), format="json"
    )
    assert wrong_first_version.status_code == 409
    assert CandidateProfile.objects.count() == 0

    client.patch(url, profile_payload(), format="json")
    duplicate_create = client.patch(url, profile_payload(version=0), format="json")
    assert duplicate_create.status_code == 409
    assert CandidateProfile.objects.get(user=user).profile_version == 1


@pytest.mark.parametrize(
    "user_kwargs, expected_status",
    [
        ({"role": User.Role.OPERATOR}, 403),
        ({"role": User.Role.ADMIN}, 403),
        ({"active": False}, 403),
    ],
)
def test_only_active_clients_can_use_self_service(user_kwargs, expected_status):
    user = make_user(**user_kwargs)
    response = client_for(user).get(reverse("candidates:profile"))
    assert response.status_code == expected_status


def test_anonymous_client_is_rejected():
    response = APIClient().get(reverse("candidates:profile"))
    assert response.status_code == 401


def test_draft_can_be_empty_but_basics_are_derived():
    user = make_user()
    response = client_for(user).patch(
        reverse("candidates:profile"),
        {
            "profile_version": 0,
            "full_name": "",
            "location": "",
            "experience_summary": "",
            "target_roles": [],
        },
        format="json",
    )

    assert response.status_code == 200
    assert response.json()["basics_complete"] is False
