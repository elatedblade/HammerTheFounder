from datetime import timedelta

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from apps.applications.models import Application
from apps.billing.models import Payment
from apps.campaigns.models import Campaign
from apps.candidates.models import CandidateProfile
from apps.companies.models import Company
from apps.jobs.models import Job
from apps.users.models import User


pytestmark = pytest.mark.django_db
BASE = "/api/v1/"


def make_user(subject, role=User.Role.CLIENT):
    return User.objects.create_user(
        "clerk", subject, email=f"{subject}@example.com", role=role
    )


def api(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.fixture
def history_world():
    owner = make_user("history-owner")
    outsider = make_user("history-outsider")
    first_operator = make_user("history-operator-one", User.Role.OPERATOR)
    second_operator = make_user("history-operator-two", User.Role.OPERATOR)
    admin = make_user("history-admin", User.Role.ADMIN)
    candidate = CandidateProfile.objects.create(
        user=owner, full_name="Ada Lovelace", location="London"
    )
    other_candidate = CandidateProfile.objects.create(
        user=outsider, full_name="Grace Hopper", location="New York"
    )
    first_campaign = Campaign.objects.create(
        candidate=candidate,
        plan=Campaign.Plan.NORMAL_APPLY,
        status=Campaign.Status.ACTIVE,
        assigned_to=first_operator,
    )
    second_campaign = Campaign.objects.create(
        candidate=candidate,
        plan=Campaign.Plan.NORMAL_APPLY,
        status=Campaign.Status.ACTIVE,
        assigned_to=second_operator,
    )
    # A second visible campaign for the first operator guards the aggregate
    # against multiplication from the candidate-visibility join.
    Campaign.objects.create(
        candidate=candidate,
        plan=Campaign.Plan.NORMAL_APPLY,
        status=Campaign.Status.ACTIVE,
        assigned_to=first_operator,
    )
    other_campaign = Campaign.objects.create(
        candidate=other_candidate,
        plan=Campaign.Plan.NORMAL_APPLY,
        status=Campaign.Status.ACTIVE,
        assigned_to=second_operator,
    )
    company = Company.objects.create(
        name="History Co", identity_key="domain:history.example"
    )
    jobs = [
        Job.objects.create(
            company=company, title=f"Role {index}", identity_key=f"history-job-{index}"
        )
        for index in range(4)
    ]
    return {
        "owner": owner,
        "outsider": outsider,
        "first_operator": first_operator,
        "second_operator": second_operator,
        "admin": admin,
        "candidate": candidate,
        "other_candidate": other_candidate,
        "first_campaign": first_campaign,
        "second_campaign": second_campaign,
        "other_campaign": other_campaign,
        "jobs": jobs,
    }


def add_application(campaign, job, status, submitted_at=None):
    return Application.objects.create(
        campaign=campaign, job=job, status=status, submitted_at=submitted_at
    )


def test_candidate_submitted_count_is_scoped_and_not_multiplied(history_world):
    world = history_world
    sent = timezone.now() - timedelta(days=1)
    add_application(world["first_campaign"], world["jobs"][0], "SUBMITTED", sent)
    add_application(world["second_campaign"], world["jobs"][1], "REJECTED", sent)
    # This status is not evidence of submission and must not inflate the count.
    add_application(world["first_campaign"], world["jobs"][2], "SAVED")

    first_result = api(world["first_operator"]).get(BASE + "admin/candidates/")
    assert first_result.status_code == 200
    assert first_result.json()[0]["applications_submitted"] == 1

    admin_result = api(world["admin"]).get(BASE + "admin/candidates/")
    assert admin_result.status_code == 200
    candidate = next(
        row for row in admin_result.json() if row["id"] == world["candidate"].pk
    )
    assert candidate["applications_submitted"] == 2


def test_candidate_history_filters_preserve_campaign_and_identity_scope(history_world):
    world = history_world
    sent = timezone.now() - timedelta(days=1)
    first_application = add_application(
        world["first_campaign"], world["jobs"][0], "SUBMITTED", sent
    )
    second_application = add_application(
        world["second_campaign"], world["jobs"][1], "SUBMITTED", sent
    )
    Payment.objects.create(campaign=world["first_campaign"], amount="10.00")
    Payment.objects.create(campaign=world["second_campaign"], amount="20.00")

    first_operator_apps = api(world["first_operator"]).get(
        BASE + "applications/", {"candidate": world["candidate"].pk}
    )
    assert [row["id"] for row in first_operator_apps.json()] == [str(first_application.pk)]

    owner_apps = api(world["owner"]).get(
        BASE + "applications/", {"candidate": world["candidate"].pk}
    )
    assert {row["id"] for row in owner_apps.json()} == {
        str(first_application.pk),
        str(second_application.pk),
    }
    assert api(world["outsider"]).get(
        BASE + "applications/", {"candidate": world["candidate"].pk}
    ).json() == []

    owner_payments = api(world["owner"]).get(
        BASE + "billing/payments/", {"candidate": world["candidate"].pk}
    )
    assert owner_payments.status_code == 200
    assert len(owner_payments.json()) == 2
    assert api(world["outsider"]).get(
        BASE + "billing/payments/", {"candidate": world["candidate"].pk}
    ).json() == []

    for route in ("applications/", "billing/payments/"):
        for invalid in ("0", "-1", "not-an-integer"):
            assert api(world["owner"]).get(
                BASE + route, {"candidate": invalid}
            ).status_code == 400


def test_payment_history_pages_all_rows_in_deterministic_order(history_world):
    world = history_world
    campaign = world["first_campaign"]
    payments = [
        Payment(campaign=campaign, amount="10.00")
        for _ in range(205)
    ]
    Payment.objects.bulk_create(payments)
    now = timezone.now()
    Payment.objects.filter(campaign=campaign).update(created_at=now)

    first = api(world["owner"]).get(
        BASE + "billing/payments/", {"limit": 200, "offset": 0}
    )
    second = api(world["owner"]).get(
        BASE + "billing/payments/", {"limit": 200, "offset": 200}
    )
    repeat = api(world["owner"]).get(
        BASE + "billing/payments/", {"limit": 200, "offset": 0}
    )
    assert first.status_code == second.status_code == 200
    assert len(first.json()) == 200
    assert len(second.json()) == 5
    assert first.json() == repeat.json()
    assert not ({row["id"] for row in first.json()} & {row["id"] for row in second.json()})
    assert "no-store" in first["Cache-Control"]


def test_candidate_search_is_server_side(history_world):
    world = history_world
    response = api(world["admin"]).get(BASE + "admin/candidates/", {"q": "grace"})
    assert response.status_code == 200
    assert [row["id"] for row in response.json()] == [world["other_candidate"].pk]


def test_overview_metrics_distinguish_lifecycle_payment_and_future_interviews(history_world):
    world = history_world
    Campaign.objects.filter(pk=world["first_campaign"].pk).update(status="READY", billing_status="ACTIVE")
    Payment.objects.create(campaign=world["first_campaign"], amount="10.00", status="PENDING")
    Payment.objects.create(campaign=world["second_campaign"], amount="20.00", status="PENDING")
    Application.objects.create(
        campaign=world["first_campaign"], job=world["jobs"][0],
        status="INTERVIEW_SCHEDULED", submitted_at=timezone.now(),
        interview_scheduled_at=timezone.now() + timedelta(days=1),
    )
    response = api(world["admin"]).get(BASE + "dashboard/", {"campaign": world["first_campaign"].pk})
    assert response.status_code == 200
    assert response.json()["campaigns"] == {"total": 1, "active": 0, "ready": 1}
    assert response.json()["payments"]["pending"] == 1
    assert response.json()["applications"]["upcoming_interviews"] == 1
    Campaign.objects.filter(pk=world["first_campaign"].pk).update(status="ACTIVE")
    assert api(world["admin"]).get(BASE + "dashboard/", {"campaign": world["first_campaign"].pk}).json()["campaigns"]["active"] == 1
