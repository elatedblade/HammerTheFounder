from datetime import date

import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from apps.campaigns.models import Campaign
from apps.candidates.models import CandidateProfile
from apps.resumes.models import Resume
from apps.users.models import User


pytestmark = pytest.mark.django_db


def make_user(subject="client", role=User.Role.CLIENT, active=True):
    return User.objects.create_user(
        "clerk", subject, email=f"{subject}@example.com", role=role, is_active=active
    )


def client_for(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


def make_profile(user, *, ready=False):
    values = {"user": user}
    if ready:
        values.update(
            full_name="Ada Lovelace",
            location="London",
            experience_summary="Builds reliable systems.",
            target_roles=["Staff Engineer"],
        )
    return CandidateProfile.objects.create(**values)


def create_payload(profile, **overrides):
    payload = {"candidate_id": profile.id, "plan": Campaign.Plan.NORMAL_APPLY}
    payload.update(overrides)
    return payload


def test_client_lists_only_owned_campaigns():
    first = make_user("first")
    second = make_user("second")
    first_profile = make_profile(first)
    second_profile = make_profile(second)
    Campaign.objects.create(candidate=first_profile, plan=Campaign.Plan.COLD_APPLY)
    Campaign.objects.create(candidate=second_profile, plan=Campaign.Plan.FULL_THROTTLE)

    response = client_for(first).get(reverse("campaigns:list"))

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["plan"] == Campaign.Plan.COLD_APPLY


def test_only_operators_and_admins_can_create_campaigns():
    client_user = make_user()
    profile = make_profile(client_user)

    response = client_for(client_user).post(
        reverse("campaigns:list"), create_payload(profile), format="json"
    )

    assert response.status_code == 403
    assert Campaign.objects.count() == 0


def test_campaign_creation_rejects_non_client_candidate_profiles():
    operator = make_user("operator", role=User.Role.OPERATOR)
    internal_profile = make_profile(make_user("internal", role=User.Role.OPERATOR))

    response = client_for(operator).post(
        reverse("campaigns:list"), create_payload(internal_profile), format="json"
    )

    assert response.status_code == 404
    assert Campaign.objects.count() == 0


def test_operator_creates_campaign_and_can_start_ready_campaign():
    candidate = make_user("candidate")
    profile = make_profile(candidate, ready=True)
    Resume.objects.create(
        candidate=profile,
        s3_key="candidates/1/resumes/one/original.pdf",
        original_filename="one.pdf",
        content_type="application/pdf",
        file_size=1024,
        upload_status=Resume.UploadStatus.UPLOADED,
    )
    operator = make_user("operator", role=User.Role.OPERATOR)
    client = client_for(operator)

    created = client.post(
        reverse("campaigns:list"),
        create_payload(profile, trial_end_date="2026-10-16", settings_json={"weekly_limit": 10}),
        format="json",
    )

    assert created.status_code == 201
    assert created.json()["status"] == Campaign.Status.READY
    assert created.json()["trial_end_date"] == "2026-10-16"
    campaign_id = created.json()["id"]

    started = client.post(reverse("campaigns:start", args=[campaign_id]))

    assert started.status_code == 200
    assert started.json()["status"] == Campaign.Status.ACTIVE
    assert started.json()["start_date"] == date.today().isoformat()
    assert started.json()["version"] == 2


def test_start_marks_incomplete_campaign_onboarding_and_returns_conflict():
    candidate = make_user("candidate")
    profile = make_profile(candidate)
    operator = make_user("operator", role=User.Role.OPERATOR)
    campaign = Campaign.objects.create(candidate=profile, plan=Campaign.Plan.NORMAL_APPLY)

    response = client_for(operator).post(
        reverse("campaigns:start", args=[campaign.id])
    )

    assert response.status_code == 409
    assert response.json()["code"] == "CAMPAIGN_NOT_READY"
    campaign.refresh_from_db()
    assert campaign.status == Campaign.Status.ONBOARDING
    assert campaign.version == 2


def test_pause_and_resume_are_explicit_state_transitions():
    candidate = make_user("candidate")
    campaign = Campaign.objects.create(
        candidate=make_profile(candidate),
        plan=Campaign.Plan.NORMAL_APPLY,
        status=Campaign.Status.ACTIVE,
    )
    operator = make_user("operator", role=User.Role.OPERATOR)
    client = client_for(operator)

    paused = client.post(reverse("campaigns:pause", args=[campaign.id]))
    resumed = client.post(reverse("campaigns:resume", args=[campaign.id]))

    assert paused.status_code == 200
    assert paused.json()["status"] == Campaign.Status.PAUSED
    assert resumed.status_code == 200
    assert resumed.json()["status"] == Campaign.Status.ACTIVE
    assert resumed.json()["version"] == 3


def test_client_cannot_read_another_candidates_campaign():
    owner = make_user("owner")
    other = make_user("other")
    campaign = Campaign.objects.create(
        candidate=make_profile(owner), plan=Campaign.Plan.NORMAL_APPLY
    )

    response = client_for(other).get(
        reverse("campaigns:detail", args=[campaign.id])
    )

    assert response.status_code == 404


@pytest.mark.parametrize("bad_plan", ["", "INVALID"])
def test_campaign_creation_rejects_invalid_plan(bad_plan):
    operator = make_user("operator", role=User.Role.OPERATOR)
    profile = make_profile(make_user("candidate"))

    response = client_for(operator).post(
        reverse("campaigns:list"), create_payload(profile, plan=bad_plan), format="json"
    )

    assert response.status_code == 400
    assert "plan" in response.json()["details"]
