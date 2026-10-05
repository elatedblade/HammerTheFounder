"""The stage editor is forward-only and records external submission explicitly."""
from datetime import timedelta

import pytest
from django.utils import timezone

from apps.applications.models import Application
from apps.applications.stages import STAGE_STATUSES
from apps.audit.models import AuditEntry
from apps.events.models import Event
from tests.test_operations_api import BASE, api, workspace

pytestmark = pytest.mark.django_db


def route(obj):
    return BASE + f"applications/{obj.pk}/stage/"


def snapshot(obj):
    obj.refresh_from_db()
    return (obj.status, obj.notes, obj.submitted_at, obj.in_progress_at,
            obj.failed_at, obj.failure_reason, obj.interview_scheduled_at, obj.updated_at,
            Event.objects.count(), AuditEntry.objects.count())


@pytest.mark.parametrize("stage,status", [
    ("SAVED", "SAVED"), ("IN_PROGRESS", "IN_PROGRESS"),
    ("UNDER_REVIEW", "IN_REVIEW"), ("INTERVIEWS", "INTERVIEW"), ("OFFERS", "OFFER"),
])
@pytest.mark.parametrize("role", ["operator", "admin"])
def test_all_five_choices_from_saved_are_consistent_with_counts_and_candidate(workspace, stage, status, role):
    owner, operator, admin, _, candidate, campaign, _, job, _ = workspace
    client = api(operator if role == "operator" else admin)
    obj = Application.objects.create(campaign=campaign, job=job)
    result = client.post(route(obj), {"stage": stage, "submission_confirmed": True, "notes": "confirmed externally"}, format="json")
    assert result.status_code == 200
    assert result.json()["stage"] == stage and result.json()["status"] == status
    obj.refresh_from_db()
    submitted = int(stage in {"UNDER_REVIEW", "INTERVIEWS", "OFFERS"})
    assert bool(obj.submitted_at) == bool(submitted)
    assert bool(obj.in_progress_at) == (stage == "IN_PROGRESS")
    assert obj.candidate_id == candidate.pk
    for identity in (owner, operator, admin):
        metrics = api(identity).get(BASE + "dashboard/").json()["applications"]
        assert metrics["stage_counts"] == {key: int(key == stage) for key in STAGE_STATUSES}
        assert metrics["submitted"] == submitted
        rows = api(identity).get(BASE + "applications/", {"stage": stage, "candidate": candidate.pk}).json()
        assert len(rows) == 1 and rows[0]["stage"] == stage
    profile = client.get(BASE + f"admin/candidates/{candidate.pk}/").json()
    assert profile["applications_submitted"] == submitted
    assert Event.objects.count() == AuditEntry.objects.count() == int(stage != "SAVED")
    if stage != "SAVED":
        event = Event.objects.get(event_type="applications.status_changed")
        assert event.payload["from"] == "SAVED" and event.payload["to"] == status
        assert AuditEntry.objects.filter(event=event, actor=operator if role == "operator" else admin).exists()


@pytest.mark.parametrize("start", ["SAVED", "DISCOVERED", "SHORTLISTED", "READY", "QUEUED", "IN_PROGRESS"])
@pytest.mark.parametrize("stage", ["UNDER_REVIEW", "INTERVIEWS", "OFFERS"])
def test_unsent_forward_jumps_require_explicit_confirmation_without_writes(workspace, start, stage):
    _, operator, _, _, _, campaign, _, job, _ = workspace
    obj = Application.objects.create(campaign=campaign, job=job, status=start, notes="keep")
    before = snapshot(obj)
    for payload in ({"stage": stage}, {"stage": stage, "submission_confirmed": False, "notes": "overwrite"}):
        result = api(operator).post(route(obj), payload, format="json")
        assert result.status_code == 409 and "Confirm" in result.json()["message"]
        assert snapshot(obj) == before
    result = api(operator).post(route(obj), {"stage": stage, "submission_confirmed": True}, format="json")
    assert result.status_code == 200 and result.json()["submitted_at"]


@pytest.mark.parametrize("start", ["IN_PROGRESS", "IN_REVIEW", "INTERVIEW", "OFFER"])
def test_regressions_preserve_all_history(workspace, start):
    _, operator, _, _, _, campaign, _, job, _ = workspace
    date = timezone.now() - timedelta(days=3)
    obj = Application.objects.create(campaign=campaign, job=job, status=start,
        submitted_at=date if start != "IN_PROGRESS" else None, in_progress_at=date,
        interview_scheduled_at=date, notes="keep")
    before = snapshot(obj)
    for stage in tuple(STAGE_STATUSES)[:tuple(STAGE_STATUSES).index({"IN_PROGRESS": "IN_PROGRESS", "IN_REVIEW": "UNDER_REVIEW", "INTERVIEW": "INTERVIEWS", "OFFER": "OFFERS"}[start])]:
        result = api(operator).post(route(obj), {"stage": stage, "submission_confirmed": True}, format="json")
        assert result.status_code == 409 and "cannot move backward" in result.json()["message"]
        assert snapshot(obj) == before


@pytest.mark.parametrize("start", ["APPLICATION_FAILED", "REJECTED", "WITHDRAWN"])
def test_historical_outcomes_remain_unchanged(workspace, start):
    _, operator, _, _, _, campaign, _, job, _ = workspace
    obj = Application.objects.create(campaign=campaign, job=job, status=start,
        failed_at=timezone.now(), failure_reason="historic", submitted_at=timezone.now())
    before = snapshot(obj)
    for stage in STAGE_STATUSES:
        assert api(operator).post(route(obj), {"stage": stage, "submission_confirmed": True}, format="json").status_code == 409
        assert snapshot(obj) == before


@pytest.mark.parametrize("stage", ["IN_PROGRESS", "UNDER_REVIEW", "INTERVIEWS", "OFFERS"])
@pytest.mark.parametrize("blocker", ["PAUSED", "COMPLETED", "CANCELLED", "CLOSED"])
def test_progress_and_first_submission_keep_campaign_and_job_guards(workspace, stage, blocker):
    _, operator, _, _, _, campaign, _, job, _ = workspace
    obj = Application.objects.create(campaign=campaign, job=job)
    if blocker == "CLOSED":
        job.status = "CLOSED"
        job.save()
    else:
        campaign.status = blocker
        campaign.save()
    before = snapshot(obj)
    assert api(operator).post(route(obj), {"stage": stage, "submission_confirmed": True}, format="json").status_code == 409
    assert snapshot(obj) == before


def test_submitted_forward_progress_preserves_first_submission_and_interview_date(workspace):
    _, operator, _, _, _, campaign, _, job, _ = workspace
    submitted = timezone.now() - timedelta(days=5)
    interview = timezone.now() - timedelta(days=1)
    obj = Application.objects.create(campaign=campaign, job=job, status="SUBMITTED", submitted_at=submitted)
    campaign.status = "PAUSED"
    campaign.save()
    job.status = "CLOSED"
    job.save()
    for stage in ("UNDER_REVIEW", "INTERVIEWS"):
        assert api(operator).post(route(obj), {"stage": stage}, format="json").status_code == 200
    obj.refresh_from_db()
    obj.status = "INTERVIEW_SCHEDULED"
    obj.interview_scheduled_at = interview
    obj.save()
    result = api(operator).post(route(obj), {"stage": "OFFERS", "notes": "offer received"}, format="json")
    assert result.status_code == 200
    obj.refresh_from_db()
    assert obj.status == "OFFER" and obj.submitted_at == submitted
    assert obj.interview_scheduled_at == interview and obj.notes == "offer received"


@pytest.mark.parametrize("status", [status for statuses in STAGE_STATUSES.values() for status in statuses])
def test_current_stage_is_idempotent_without_canonicalizing_or_auditing(workspace, status):
    _, operator, _, _, _, campaign, _, job, _ = workspace
    obj = Application.objects.create(campaign=campaign, job=job, status=status,
        interview_scheduled_at=timezone.now() if status == "INTERVIEW_SCHEDULED" else None, notes="keep")
    stage = next(stage for stage, statuses in STAGE_STATUSES.items() if status in statuses)
    before = snapshot(obj)
    for _ in range(2):
        assert api(operator).post(route(obj), {"stage": stage, "notes": "ignored"}, format="json").status_code == 200
        assert snapshot(obj) == before


def test_clients_and_unassigned_operators_cannot_edit_stage(workspace):
    owner, operator, admin, other, _, campaign, _, job, _ = workspace
    obj = Application.objects.create(campaign=campaign, job=job)
    before = snapshot(obj)
    assert api(owner).post(route(obj), {"stage": "OFFERS", "submission_confirmed": True}, format="json").status_code == 403
    assert api(other).post(route(obj), {"stage": "OFFERS", "submission_confirmed": True}, format="json").status_code == 404
    campaign.assigned_to = None
    campaign.save()
    assert api(operator).post(route(obj), {"stage": "OFFERS", "submission_confirmed": True}, format="json").status_code == 404
    assert snapshot(obj) == before
    assert api(admin).post(route(obj), {"stage": "OFFERS", "submission_confirmed": True}, format="json").status_code == 200


@pytest.mark.parametrize("payload", [
    {}, {"stage": "saved"}, {"stage": "SUBMITTED"}, {"stage": "REJECTED"}, {"stage": None},
    {"stage": "OFFERS", "status": "OFFER"}, {"stage": "SAVED", "interview_scheduled_at": None},
    {"stage": "OFFERS", "submission_confirmed": "true"}, {"stage": "OFFERS", "submission_confirmed": 1},
    {"stage": "OFFERS", "submission_confirmed": None}, {"stage": "SAVED", "notes": "x" * 10001},
])
def test_invalid_stage_fields_are_400_and_do_not_write(workspace, payload):
    _, operator, _, _, _, campaign, _, job, _ = workspace
    obj = Application.objects.create(campaign=campaign, job=job)
    before = snapshot(obj)
    assert api(operator).post(route(obj), payload, format="json").status_code == 400
    assert snapshot(obj) == before
