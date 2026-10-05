"""Stage projections must agree across lists and counts without rewriting history."""
from datetime import timedelta

import pytest
from django.utils import timezone

from apps.applications.models import Application
from apps.applications.stages import STAGE_STATUSES, application_stage
from apps.campaigns.models import Campaign
from apps.candidates.models import CandidateProfile
from apps.jobs.models import Job
from tests.test_operations_api import BASE, api, user, workspace

pytestmark = pytest.mark.django_db


def applications_for_all_states(campaign, company):
    objects = {}
    for status in Application.Status.values:
        job = Job.objects.create(company=company, title=status, identity_key=f"stage-{status}")
        objects[status] = Application.objects.create(
            campaign=campaign, job=job, status=status,
            notes="private notes", source_reference="private receipt", failure_reason="private failure",
            interview_scheduled_at=timezone.now() + timedelta(days=1) if status == "INTERVIEW_SCHEDULED" else None,
        )
    return objects


def test_every_legacy_state_has_consistent_stage_counts_filters_and_history(workspace):
    owner, operator, admin, other, candidate, campaign, company, *_ = workspace
    objects = applications_for_all_states(campaign, company)
    # A withdrawn submitted application still contributes to lifetime submissions.
    objects["WITHDRAWN"].submitted_at = timezone.now()
    objects["WITHDRAWN"].save()
    expected = {stage: len(statuses) for stage, statuses in STAGE_STATUSES.items()}
    for identity in (owner, operator, admin):
        client = api(identity)
        metrics = client.get(BASE + "dashboard/", {"campaign": str(campaign.pk)}).json()["applications"]
        assert metrics["stage_counts"] == expected
        assert metrics["total"] == 15
        assert metrics["submitted"] == 8
        assert metrics["by_status"] == {status: 1 for status in Application.Status.values}
        assert sum(metrics["stage_counts"].values()) == metrics["total"] - 3
        # Scheduled/upcoming counters are intentional subsets of INTERVIEWS,
        # while submitted is lifetime evidence, never a sixth pipeline stage.
        assert metrics["interviews"] == metrics["stage_counts"]["INTERVIEWS"] == 2
        assert metrics["interview_scheduled"] == metrics["upcoming_interviews"] == 1
        assert set(metrics["stage_counts"]) == {"SAVED", "IN_PROGRESS", "UNDER_REVIEW", "INTERVIEWS", "OFFERS"}
        for stage, statuses in STAGE_STATUSES.items():
            rows = client.get(BASE + "applications/", {"stage": stage, "candidate": candidate.pk, "campaign": str(campaign.pk)}).json()
            assert {row["status"] for row in rows} == set(statuses)
            assert len(rows) == metrics["stage_counts"][stage]
            assert all(row["stage"] == stage for row in rows)
            nested = client.get(BASE + f"campaigns/{campaign.pk}/applications/", {"stage": stage}).json()
            assert {row["id"] for row in nested} == {row["id"] for row in rows}
        for status, obj in objects.items():
            rows = client.get(BASE + "applications/", {"status": status}).json()
            assert len(rows) == 1 and rows[0]["stage"] == application_stage(status)
            obj.refresh_from_db()
            assert obj.status == status
    assert api(other).get(BASE + "applications/", {"stage": "SAVED", "candidate": candidate.pk}).json() == []
    assert api(other).get(BASE + "dashboard/").json()["applications"]["stage_counts"] == dict.fromkeys(STAGE_STATUSES, 0)
    for row in api(owner).get(BASE + "applications/").json():
        assert not {"candidate_id", "candidate_name", "candidate_email", "notes", "source_reference", "failure_reason"} & row.keys()


def test_stage_filters_intersect_legacy_status_candidate_and_permissions(workspace):
    owner, operator, admin, other, candidate, campaign, company, job, _ = workspace
    Application.objects.create(campaign=campaign, job=job, status="SAVED")
    stranger = user("stage-outsider")
    profile = CandidateProfile.objects.create(user=stranger, full_name="Other")
    hidden_campaign = Campaign.objects.create(candidate=profile, plan="NORMAL_APPLY", status="ACTIVE", assigned_to=other)
    second_job = Job.objects.create(company=company, title="Hidden", identity_key="stage-hidden")
    hidden = Application.objects.create(campaign=hidden_campaign, job=second_job)
    for identity in (owner, operator):
        client = api(identity)
        assert len(client.get(BASE + "applications/", {"stage": "SAVED"}).json()) == 1
        assert client.get(BASE + "applications/", {"stage": "SAVED", "candidate": profile.pk}).json() == []
        assert client.get(BASE + "applications/", {"stage": "SAVED", "campaign": str(hidden_campaign.pk)}).status_code == 404
        assert client.get(BASE + f"applications/{hidden.pk}/", {"stage": "SAVED"}).status_code == 404
        assert client.get(BASE + "applications/", {"stage": "SAVED", "status": "IN_PROGRESS"}).json() == []
        for invalid in ("", "saved", "REJECTED", "UNKNOWN"):
            result = client.get(BASE + "applications/", {"stage": invalid})
            assert result.status_code == 400 and "stage" in result.json()["details"]
    assert len(api(admin).get(BASE + "applications/", {"stage": "SAVED", "candidate": profile.pk}).json()) == 1


@pytest.mark.parametrize("status", ["SAVED", "DISCOVERED", "SHORTLISTED", "READY", "QUEUED"])
def test_start_progress_and_explicit_submission_precede_stage_aliases(workspace, status):
    owner, operator, _, _, _, campaign, _, job, _ = workspace
    obj = Application.objects.create(campaign=campaign, job=job, status=status)
    client = api(operator)
    route = BASE + f"applications/{obj.pk}/transition/"
    assert client.post(route, {"status": "UNDER_REVIEW"}, format="json").status_code == 409
    result = client.post(route, {"status": "IN_PROGRESS"}, format="json")
    assert result.status_code == 200 and result.json()["stage"] == "IN_PROGRESS"
    assert result.json()["submitted_at"] is None
    assert client.get(BASE + "dashboard/").json()["applications"]["submitted"] == 0
    assert client.post(route, {"status": "UNDER_REVIEW"}, format="json").status_code == 409
    result = client.post(route, {"status": "SUBMITTED"}, format="json")
    assert result.status_code == 200 and result.json()["stage"] == "UNDER_REVIEW"
    timestamp = result.json()["submitted_at"]
    for alias, legacy in (("UNDER_REVIEW", "IN_REVIEW"), ("INTERVIEWS", "INTERVIEW"), ("OFFERS", "OFFER")):
        result = client.post(route, {"status": alias}, format="json")
        assert result.status_code == 200
        assert result.json()["status"] == legacy and result.json()["stage"] == alias
        assert result.json()["submitted_at"] == timestamp
    assert client.get(BASE + "dashboard/").json()["applications"]["submitted"] == 1
    assert api(owner).post(route, {"status": "OFFERS"}, format="json").status_code == 403


@pytest.mark.parametrize("blocker", ["PAUSED", "CLOSED"])
def test_start_progress_preserves_campaign_and_job_guards(workspace, blocker):
    _, operator, _, _, _, campaign, _, job, _ = workspace
    obj = Application.objects.create(campaign=campaign, job=job)
    if blocker == "PAUSED":
        campaign.status = blocker
        campaign.save()
    else:
        job.status = blocker
        job.save()
    result = api(operator).post(BASE + f"applications/{obj.pk}/transition/", {"status": "IN_PROGRESS"}, format="json")
    assert result.status_code == 409
    obj.refresh_from_db()
    assert obj.status == "SAVED" and obj.in_progress_at is None and obj.submitted_at is None


def test_stage_is_computed_and_not_writable(workspace):
    _, operator, _, _, _, campaign, _, job, _ = workspace
    client = api(operator)
    payload = {"campaign": str(campaign.pk), "job": str(job.pk), "stage": "OFFERS"}
    assert client.post(BASE + "applications/", payload, format="json").status_code == 400
    obj = Application.objects.create(campaign=campaign, job=job)
    assert client.patch(BASE + f"applications/{obj.pk}/", {"stage": "OFFERS"}, format="json").status_code == 400


def test_future_interviews_are_a_current_stage_subset_not_extra_pipeline_rows(workspace):
    owner, _, _, _, _, campaign, company, *_ = workspace
    now = timezone.now()
    for index, (status, date) in enumerate([
        ("INTERVIEW", now + timedelta(days=1)),
        ("INTERVIEW_SCHEDULED", now + timedelta(days=1)),
        ("INTERVIEW_SCHEDULED", now - timedelta(days=1)),
        ("OFFER", now + timedelta(days=1)),
        ("WITHDRAWN", now + timedelta(days=1)),
    ]):
        job = Job.objects.create(company=company, title="Synthetic interview", identity_key=f"subset-{index}")
        Application.objects.create(campaign=campaign, job=job, status=status,
                                   submitted_at=now, interview_scheduled_at=date)
    metrics = api(owner).get(BASE + "dashboard/").json()["applications"]
    assert metrics["total"] == metrics["submitted"] == 5
    assert metrics["stage_counts"] == {"SAVED": 0, "IN_PROGRESS": 0, "UNDER_REVIEW": 0, "INTERVIEWS": 3, "OFFERS": 1}
    assert metrics["upcoming_interviews"] == 1
    assert metrics["interview_scheduled"] == 2
    assert metrics["interviews"] == 3
    rows = api(owner).get(BASE + "applications/", {"stage": "INTERVIEWS"}).json()
    assert len(rows) == 3 and len({row["id"] for row in rows}) == 3
