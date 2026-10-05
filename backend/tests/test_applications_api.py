import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from apps.applications.models import Application
from apps.campaigns.models import Campaign
from apps.candidates.models import CandidateProfile
from apps.companies.models import Company
from apps.jobs.models import Job
from apps.users.models import User


pytestmark = pytest.mark.django_db


def make_user(subject, role=User.Role.CLIENT):
    return User.objects.create_user(
        "clerk", subject, email=f"{subject}@example.com", role=role
    )


def client_for(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


def make_application_fixtures(subject="candidate"):
    user = make_user(subject)
    candidate = CandidateProfile.objects.create(user=user)
    campaign = Campaign.objects.create(
        candidate=candidate, plan=Campaign.Plan.NORMAL_APPLY
    )
    company = Company.objects.create(name=f"{subject} company")
    job = Job.objects.create(
        company=company,
        external_source=f"source-{subject}",
        external_id="job-1",
        title="Staff Engineer",
    )
    return user, candidate, campaign, job


def create_payload(campaign, job, **overrides):
    payload = {"campaign_id": str(campaign.id), "job_id": str(job.id)}
    payload.update(overrides)
    return payload


def test_operator_creates_application_and_duplicate_candidate_job_is_blocked():
    _, _, campaign, job = make_application_fixtures()
    operator = make_user("operator", User.Role.OPERATOR)
    client = client_for(operator)

    created = client.post(
        reverse("applications:list"),
        create_payload(campaign, job, source_reference="greenhouse/job-1"),
        format="json",
    )
    duplicate = client.post(
        reverse("applications:list"), create_payload(campaign, job), format="json"
    )

    assert created.status_code == 201
    assert created.json()["status"] == Application.Status.DISCOVERED
    assert created.json()["operator_id"] == operator.id
    assert duplicate.status_code == 409
    assert duplicate.json()["code"] == "APPLICATION_DUPLICATE"
    assert Application.objects.count() == 1


def test_application_transitions_follow_documented_graph_and_set_submitted_at():
    _, _, campaign, job = make_application_fixtures()
    operator = make_user("operator", User.Role.OPERATOR)
    client = client_for(operator)
    created = client.post(
        reverse("applications:list"), create_payload(campaign, job), format="json"
    )
    application_id = created.json()["id"]

    for status in (
        Application.Status.SHORTLISTED,
        Application.Status.QUEUED,
        Application.Status.IN_PROGRESS,
        Application.Status.SUBMITTED,
    ):
        response = client.post(
            reverse("applications:transition", args=[application_id]),
            {"status": status},
            format="json",
        )
        assert response.status_code == 200
        assert response.json()["status"] == status

    assert response.json()["submitted_at"] is not None


def test_invalid_application_transition_returns_conflict_envelope():
    _, _, campaign, job = make_application_fixtures()
    operator = make_user("operator", User.Role.OPERATOR)
    application = Application.objects.create(
        campaign=campaign, job=job, operator=operator
    )

    response = client_for(operator).post(
        reverse("applications:transition", args=[application.id]),
        {"status": Application.Status.OFFER},
        format="json",
    )

    assert response.status_code == 409
    assert response.json()["code"] == "INVALID_APPLICATION_TRANSITION"


def test_clients_read_only_applications_under_their_own_campaigns():
    owner, _, campaign, job = make_application_fixtures("owner")
    other, _, other_campaign, other_job = make_application_fixtures("other")
    operator = make_user("operator", User.Role.OPERATOR)
    operator_client = client_for(operator)
    first = operator_client.post(
        reverse("applications:list"), create_payload(campaign, job), format="json"
    )
    second = operator_client.post(
        reverse("applications:list"),
        create_payload(other_campaign, other_job),
        format="json",
    )

    own = client_for(owner).get(reverse("applications:list"))
    foreign = client_for(other).get(
        reverse("applications:detail", args=[first.json()["id"]])
    )
    forbidden_create = client_for(owner).post(
        reverse("applications:list"), create_payload(campaign, job), format="json"
    )

    assert own.status_code == 200
    assert [item["id"] for item in own.json()] == [first.json()["id"]]
    assert foreign.status_code == 404
    assert forbidden_create.status_code == 403
    assert second.status_code == 201


def test_campaign_application_list_hides_inaccessible_campaigns():
    owner, _, campaign, job = make_application_fixtures("owner")
    other, _, other_campaign, other_job = make_application_fixtures("other")
    operator = make_user("operator", User.Role.OPERATOR)
    operator_client = client_for(operator)
    operator_client.post(
        reverse("applications:list"), create_payload(campaign, job), format="json"
    )
    empty_own_campaign = Campaign.objects.create(
        candidate=CandidateProfile.objects.get(user=owner),
        plan=Campaign.Plan.COLD_APPLY,
    )

    empty = client_for(owner).get(
        reverse("applications:campaign-list", args=[empty_own_campaign.id])
    )
    hidden = client_for(other).get(
        reverse("applications:campaign-list", args=[campaign.id])
    )

    assert empty.status_code == 200
    assert empty.json() == []
    assert hidden.status_code == 404
