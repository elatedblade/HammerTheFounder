import pytest
from datetime import timedelta
from django.utils import timezone
from django.db import transaction, IntegrityError
from rest_framework.test import APIClient
from apps.users.models import User
from apps.candidates.models import CandidateProfile
from apps.campaigns.models import Campaign
from apps.companies.models import Company
from apps.jobs.models import Job
from apps.applications.models import Application
from apps.contacts.models import Contact
from apps.outreach.models import Outreach, Suppression
from apps.tasks.models import HumanTask
from apps.events.models import Event
from apps.audit.models import AuditEntry
from apps.events.services import record_event
from apps.resumes.models import Resume

pytestmark = pytest.mark.django_db
BASE = "/api/v1/"


def user(name, role="CLIENT", active=True):
    return User.objects.create_user("clerk", name, email=f"{name}@example.com", role=role, is_active=active)


def api(identity):
    client = APIClient()
    client.force_authenticate(identity)
    return client


@pytest.fixture
def workspace():
    owner = user("owner")
    operator = user("operator", "OPERATOR")
    admin = user("admin", "ADMIN")
    other = user("other", "OPERATOR")
    candidate = CandidateProfile.objects.create(user=owner, full_name="Ada", location="London", experience_summary="Engineer", target_roles=["Engineer"])
    campaign = Campaign.objects.create(candidate=candidate, plan="FULL_THROTTLE", status="ACTIVE", assigned_to=operator)
    company = Company.objects.create(name="Acme", identity_key="domain:acme.example")
    job = Job.objects.create(company=company, title="Engineer", identity_key="job-1")
    contact = Contact.objects.create(company=company, name="Founder", email="founder@acme.example", identity_key="contact-1")
    return owner, operator, admin, other, candidate, campaign, company, job, contact


def test_operator_scope_applies_to_reads_and_all_lifecycle_writes(workspace):
    owner, operator, admin, other, candidate, campaign, company, job, contact = workspace
    client = api(other)
    assert client.get(BASE + "campaigns/").json() == []
    assert client.get(BASE + f"campaigns/{campaign.pk}/").status_code == 404
    assert client.post(BASE + f"campaigns/{campaign.pk}/pause/").status_code == 404
    assert client.patch(BASE + f"campaigns/{campaign.pk}/", {"plan": "NORMAL_APPLY"}, format="json").status_code == 404
    assert client.get(BASE + f"admin/candidates/{candidate.pk}/").status_code == 404
    assert client.post(BASE + "applications/", {"campaign": str(campaign.pk), "job": str(job.pk)}, format="json").status_code == 404
    assert api(operator).patch(BASE + f"campaigns/{campaign.pk}/", {"assigned_to": other.pk}, format="json").status_code == 403
    assert api(admin).patch(BASE + f"campaigns/{campaign.pk}/", {"assigned_to": other.pk}, format="json").status_code == 200
    assert api(operator).get(BASE + f"campaigns/{campaign.pk}/").status_code == 404


def test_unassigned_intake_is_visible_but_unassigned_active_is_not(workspace):
    owner, operator, admin, other, candidate, campaign, *_ = workspace
    intake = Campaign.objects.create(candidate=candidate, plan="NORMAL_APPLY", status="DRAFT")
    assert api(other).get(BASE + f"campaigns/{intake.pk}/").status_code == 200
    intake.status = "ACTIVE"
    intake.save()
    assert api(other).get(BASE + f"campaigns/{intake.pk}/").status_code == 404


def test_application_manual_lifecycle_duplicate_and_sanitized_client_read(workspace):
    owner, operator, admin, other, candidate, campaign, company, job, _ = workspace
    client = api(operator)
    payload = {"campaign": str(campaign.pk), "job": str(job.pk), "notes": "private QA", "source_reference": "internal receipt"}
    created = client.post(BASE + "applications/", payload, format="json")
    assert created.status_code == 201
    application_id = created.json()["id"]
    assert client.post(BASE + "applications/", payload, format="json").status_code == 409
    route = BASE + f"applications/{application_id}/transition/"
    assert client.post(route, {"status": "OFFER"}, format="json").status_code == 409
    for status in ("READY", "SUBMITTED", "IN_REVIEW", "INTERVIEW", "OFFER"):
        assert client.post(route, {"status": status}, format="json").status_code == 200
    application = Application.objects.get(pk=application_id)
    assert application.submitted_at is not None
    result = api(owner).get(BASE + f"applications/{application_id}/").json()
    assert "notes" not in result and "source_reference" not in result
    assert api(owner).post(route, {"status": "WITHDRAWN"}, format="json").status_code == 403
    assert api(other).get(BASE + f"applications/{application_id}/").status_code == 404
    event = Event.objects.filter(event_type="applications.status_changed").first()
    assert event.actor == operator
    assert AuditEntry.objects.filter(event=event, actor=operator).exists()


def test_client_cannot_access_internal_catalog_queue_or_audit(workspace):
    owner, *_ = workspace
    for route in ("companies/", "jobs/", "contacts/", "suppression/", "outreach/templates/", "admin/tasks/", "admin/audit/", "admin/candidates/", "admin/operators/"):
        assert api(owner).get(BASE + route).status_code == 403
    disabled = user("disabled", "ADMIN", active=False)
    assert api(disabled).get(BASE + "dashboard/").status_code == 403


def test_company_and_job_normalized_dedup(workspace):
    _, operator, _, _, _, _, company, _, _ = workspace
    client = api(operator)
    data = {"name": "Example", "website": "https://EXAMPLE.com/?utm_source=test"}
    assert client.post(BASE + "companies/", data, format="json").status_code == 201
    data["website"] = "https://www.example.com/"
    assert client.post(BASE + "companies/", data, format="json").status_code == 409
    job = {"company": str(company.pk), "title": "Developer", "canonical_url": "https://jobs.example.com/roles/1?utm_source=a#apply"}
    assert client.post(BASE + "jobs/", job, format="json").status_code == 201
    job["canonical_url"] = "https://jobs.example.com/roles/1"
    assert client.post(BASE + "jobs/", job, format="json").status_code == 409
    assert client.post(BASE + "jobs/", {"company": str(company.pk), "title": "Bad", "external_source": "board"}, format="json").status_code == 400


@pytest.mark.parametrize("prepare_first", [False, True])
def test_outreach_preparation_and_suppression_blocks_manual_sent(workspace, prepare_first):
    owner, operator, admin, _, _, campaign, _, _, contact = workspace
    client = api(operator)
    data = {"campaign": str(campaign.pk), "contact": str(contact.pk), "channel": "EMAIL", "subject": "Hello", "body": "A reviewed introduction", "notes": "internal"}
    result = client.post(BASE + "outreach/", data, format="json")
    assert result.status_code == 201
    oid = result.json()["id"]
    route = BASE + f"outreach/{oid}/transition/"
    if prepare_first:
        assert client.post(route, {"status": "READY"}, format="json").status_code == 200
    assert client.post(BASE + "suppression/", {"email": "FOUNDER@acme.example", "reason": "Opted out"}, format="json").status_code == 201
    assert client.post(route, {"status": "SENT"}, format="json").status_code == 409
    assert Outreach.objects.get(pk=oid).sent_at is None
    assert client.post(BASE + "outreach/", data, format="json").status_code == 409
    visible = api(owner).get(BASE + "outreach/").json()[0]
    for private in ("body", "subject", "notes", "thread_reference", "contact"):
        assert private not in visible


@pytest.mark.parametrize("plan", ["NORMAL_APPLY", "COLD_APPLY", "FULL_THROTTLE"])
@pytest.mark.parametrize("channel", ["EMAIL", "LINKEDIN", "WHATSAPP"])
def test_manual_outreach_sent_then_responded_is_visible_in_customer_dashboard(workspace, plan, channel):
    owner, operator, _, other, _, campaign, _, _, contact = workspace
    campaign.plan = plan
    campaign.save()
    contact.email = ""
    contact.profile_url = ""
    contact.save()
    outreach = Outreach.objects.create(campaign=campaign, contact=contact, channel=channel, body="Manual external outreach")
    route = BASE + f"outreach/{outreach.pk}/transition/"
    client = api(operator)
    assert client.post(route, {"status": "REPLIED"}, format="json").status_code == 409
    assert api(owner).post(route, {"status": "SENT"}, format="json").status_code == 403
    assert api(other).post(route, {"status": "SENT"}, format="json").status_code == 404
    sent = client.post(route, {"status": "SENT", "notes": "Operator-only note"}, format="json")
    assert sent.status_code == 200, sent.json()
    outreach.refresh_from_db()
    assert outreach.status == "SENT" and outreach.sent_at is not None
    sent_at = outreach.sent_at
    assert api(owner).get(BASE + "dashboard/").json()["outreach"]["sent"] == 1
    result = api(owner).get(BASE + f"outreach/{outreach.pk}/").json()
    assert result["status"] == "SENT" and result["sent_at"]
    assert "notes" not in result and "body" not in result
    response = client.post(route, {"status": "REPLIED"}, format="json")
    assert response.status_code == 200, response.json()
    outreach.refresh_from_db()
    assert outreach.status == "REPLIED" and outreach.reply_at is not None
    assert outreach.sent_at == sent_at
    result = api(owner).get(BASE + "outreach/?status=REPLIED").json()
    assert len(result) == 1 and result[0]["status"] == "REPLIED" and result[0]["reply_at"]
    metrics = api(owner).get(BASE + "dashboard/").json()["outreach"]
    assert metrics["sent"] == 0 and metrics["replies"] == 1
    assert metrics["sent_lifetime"] == metrics["replied_lifetime"] == 1
    assert api(other).get(BASE + f"outreach/{outreach.pk}/").status_code == 404
    event = Event.objects.filter(event_type="outreach.status_changed", payload__to="REPLIED").first()
    assert event is not None and AuditEntry.objects.filter(event=event, actor=operator).exists()


def test_outreach_candidate_filter_intersects_candidate_and_campaign_visibility(workspace):
    owner, operator, _, other, candidate, campaign, _, _, contact = workspace
    other_owner = user("other-owner")
    other_candidate = CandidateProfile.objects.create(
        user=other_owner, full_name="Grace", location="Paris", experience_summary="Engineer", target_roles=["Engineer"]
    )
    other_company = Company.objects.create(name="Other Co", identity_key="domain:other.example")
    other_contact = Contact.objects.create(
        company=other_company, name="Other Founder", email="other@other.example", identity_key="contact-other"
    )
    split_company = Company.objects.create(name="Split Co", identity_key="domain:split.example")
    split_contact = Contact.objects.create(
        company=split_company, name="Split Founder", email="split@split.example", identity_key="contact-split"
    )
    split_campaign = Campaign.objects.create(
        candidate=candidate, plan="FULL_THROTTLE", status="ACTIVE", assigned_to=other
    )
    other_campaign = Campaign.objects.create(
        candidate=other_candidate, plan="FULL_THROTTLE", status="ACTIVE", assigned_to=operator
    )
    own = Outreach.objects.create(campaign=campaign, contact=contact, channel="EMAIL", status="REPLIED")
    hidden_same_candidate = Outreach.objects.create(
        campaign=split_campaign, contact=split_contact, channel="EMAIL", status="REPLIED"
    )
    other_record = Outreach.objects.create(
        campaign=other_campaign, contact=other_contact, channel="EMAIL", status="REPLIED"
    )

    operator_rows = api(operator).get(BASE + "outreach/", {"candidate": candidate.pk, "stage": "RESPONDED"})
    assert operator_rows.status_code == 200
    assert [row["id"] for row in operator_rows.json()] == [str(own.pk)]
    assert [row["id"] for row in api(other).get(BASE + "outreach/", {"candidate": candidate.pk}).json()] == [
        str(hidden_same_candidate.pk)
    ]

    assert {row["id"] for row in api(owner).get(BASE + "outreach/", {"candidate": candidate.pk}).json()} == {
        str(own.pk), str(hidden_same_candidate.pk)
    }
    assert [row["id"] for row in api(other_owner).get(BASE + "outreach/", {"candidate": other_candidate.pk}).json()] == [str(other_record.pk)]
    assert api(owner).get(BASE + "outreach/", {"candidate": other_candidate.pk}).json() == []
    assert [row["id"] for row in api(operator).get(BASE + "outreach/", {"candidate": other_candidate.pk}).json()] == [str(other_record.pk)]
    assert api(other).get(BASE + "outreach/", {"candidate": other_candidate.pk}).json() == []
    assert api(operator).get(BASE + "outreach/", {"candidate": candidate.pk, "campaign": other_campaign.pk}).json() == []
    assert api(operator).get(BASE + f"campaigns/{campaign.pk}/outreach/", {"candidate": other_candidate.pk}).json() == []
    assert api(operator).get(BASE + "outreach/", {"candidate": candidate.pk, "campaign": split_campaign.pk}).status_code == 404

    paged = api(operator).get(BASE + "outreach/", {"candidate": candidate.pk, "limit": 1, "offset": 0})
    assert paged.status_code == 200 and [row["id"] for row in paged.json()] == [str(own.pk)]


@pytest.mark.parametrize("candidate", ["", "0", "-1", "abc", "1.5", "true"])
def test_outreach_candidate_filter_rejects_invalid_ids(workspace, candidate):
    _, operator, *_ = workspace
    response = api(operator).get(BASE + "outreach/", {"candidate": candidate})
    assert response.status_code == 400
    assert "candidate" in response.json()["details"]


def test_outreach_candidate_stage_and_pagination_intersect(workspace):
    _, operator, _, _, candidate, campaign, _, _, contact = workspace
    for channel, status in (("EMAIL", "REPLIED"), ("LINKEDIN", "POSITIVE_REPLY"), ("WHATSAPP", "SENT")):
        Outreach.objects.create(campaign=campaign, contact=contact, channel=channel, status=status)
    expected = [str(pk) for pk in Outreach.objects.filter(status__in=("REPLIED", "POSITIVE_REPLY")).values_list("pk", flat=True)]
    client = api(operator)
    params = {"candidate": candidate.pk, "stage": "RESPONDED", "limit": 1}
    first = client.get(BASE + "outreach/", params)
    second = client.get(BASE + "outreach/", {**params, "offset": 1})
    exhausted = client.get(BASE + "outreach/", {**params, "offset": 2})
    assert first.status_code == second.status_code == exhausted.status_code == 200
    assert [row["id"] for row in first.json() + second.json()] == expected
    assert exhausted.json() == []
    response = client.get(BASE + "outreach/", {"candidate": candidate.pk, "stage": "RESPONDED", "status": "SENT"})
    assert response.status_code == 200 and response.json() == []


def test_outreach_candidate_filter_intersects_operational_candidate_scope(workspace):
    owner, operator, _, _, candidate, campaign, _, _, contact = workspace
    Outreach.objects.create(campaign=campaign, contact=contact, status="REPLIED")
    owner.is_active = False
    owner.save(update_fields=["is_active"])
    response = api(operator).get(BASE + "outreach/", {"candidate": candidate.pk})
    assert response.status_code == 200 and response.json() == []


@pytest.mark.parametrize("status", ["DRAFT", "TARGET_IDENTIFIED", "CONTACT_VERIFIED", "DRAFTED", "REVIEW_REQUIRED", "READY"])
def test_manual_sent_available_from_each_outreach_preparation_status(workspace, status):
    _, operator, _, _, _, campaign, _, _, contact = workspace
    outreach = Outreach.objects.create(campaign=campaign, contact=contact, channel="EMAIL", body="Manual outreach", status=status)
    response = api(operator).post(BASE + f"outreach/{outreach.pk}/transition/", {"status": "SENT"}, format="json")
    assert response.status_code == 200, response.json()


@pytest.mark.parametrize("status", ["PAUSED", "DRAFT", "COMPLETED", "CANCELLED"])
def test_manual_sent_still_requires_active_outreach_campaign(workspace, status):
    _, operator, _, _, _, campaign, _, _, contact = workspace
    outreach = Outreach.objects.create(campaign=campaign, contact=contact, channel="EMAIL", body="Manual outreach")
    campaign.status = status
    campaign.save()
    response = api(operator).post(BASE + f"outreach/{outreach.pk}/transition/", {"status": "SENT"}, format="json")
    assert response.status_code == 409
    outreach.refresh_from_db()
    assert outreach.status == "DRAFT" and outreach.sent_at is None


def test_human_task_claim_complete_and_assignment_roles(workspace):
    _, operator, admin, other, _, campaign, *_ = workspace
    client = api(operator)
    response = client.post(BASE + "admin/tasks/", {"campaign": str(campaign.pk), "task_type": "QA", "priority": 1, "payload_json": {"check": "profile"}}, format="json")
    assert response.status_code == 201
    tid = response.json()["id"]
    assert client.post(BASE + f"admin/tasks/{tid}/complete/", {}, format="json").status_code == 409
    assert client.post(BASE + f"admin/tasks/{tid}/claim/", {}, format="json").status_code == 200
    assert client.post(BASE + f"admin/tasks/{tid}/claim/", {}, format="json").status_code == 409
    assert client.patch(BASE + f"admin/tasks/{tid}/", {"priority": 2}, format="json").status_code == 403
    assert api(admin).patch(BASE + f"admin/tasks/{tid}/", {"priority": 2}, format="json").status_code == 200
    done = client.post(BASE + f"admin/tasks/{tid}/complete/", {"notes": "Checked"}, format="json")
    assert done.status_code == 200 and done.json()["completed_at"]
    assert HumanTask.objects.get(pk=tid).completion_notes == "Checked"


def test_review_readiness_and_self_edit_invalidates_approval(workspace):
    owner, operator, _, _, candidate, campaign, *_ = workspace
    campaign.status = "DRAFT"
    campaign.save()
    client = api(operator)
    review = BASE + f"admin/candidates/{candidate.pk}/"
    assert client.patch(review, {"review_status": "APPROVED"}, format="json").status_code == 400
    Resume.objects.create(candidate=candidate, s3_key="private/file.pdf", original_filename="file.pdf", content_type="application/pdf", file_size=100, upload_status="UPLOADED")
    assert client.patch(review, {"review_status": "APPROVED"}, format="json").status_code == 200
    assert client.post(BASE + f"campaigns/{campaign.pk}/start/").status_code == 200
    from apps.candidates.services import upsert_own_profile
    upsert_own_profile(user=owner, data={"profile_version": candidate.profile_version, "notice_period": "30 days"})
    candidate.refresh_from_db()
    assert candidate.review_status == "PENDING" and candidate.reviewed_at is None


def test_only_admin_can_assign_intake_before_operator_starts(workspace):
    _, operator, admin, _, candidate, campaign, *_ = workspace
    candidate.review_status = "APPROVED"
    candidate.save()
    Resume.objects.create(candidate=candidate, s3_key="private/approved.pdf", original_filename="approved.pdf", content_type="application/pdf", file_size=100, upload_status="UPLOADED")
    campaign.status = "DRAFT"
    campaign.assigned_to = None
    campaign.save()
    route = BASE + f"campaigns/{campaign.pk}/"
    assert api(operator).post(route + "start/").status_code == 409
    campaign.refresh_from_db()
    assert campaign.assigned_to_id is None
    assert api(admin).patch(route, {"assigned_to": operator.pk}, format="json").status_code == 200
    assert api(operator).post(route + "start/").status_code == 200


def test_events_safe_timeline_metrics_and_transactional_rollback(workspace):
    owner, operator, admin, _, _, campaign, _, job, _ = workspace
    application = Application.objects.create(campaign=campaign, job=job, status="INTERVIEW")
    safe = record_event(campaign=campaign, actor=operator, event_type="public", summary="Interview scheduled", payload={"private": "secret"})
    record_event(campaign=campaign, actor=operator, event_type="private", summary="Internal QA", client_visible=False)
    result = api(owner).get(BASE + f"events/?campaign={campaign.pk}").json()
    assert len(result) == 1 and result[0]["id"] == str(safe.pk)
    assert "payload" not in result[0] and "actor" not in result[0]
    metrics = api(owner).get(BASE + "dashboard/").json()
    assert metrics["applications"]["interviews"] == 1
    before = Event.objects.count()
    with pytest.raises(RuntimeError):
        with transaction.atomic():
            record_event(campaign=campaign, event_type="rollback", summary="Must roll back")
            raise RuntimeError()
    assert Event.objects.count() == before
    assert not AuditEntry.objects.filter(action="rollback").exists()


def test_terminal_campaign_rejects_new_work_and_duplicate_transition(workspace):
    _, operator, _, _, _, campaign, _, job, _ = workspace
    client = api(operator)
    assert client.post(BASE + f"campaigns/{campaign.pk}/complete/").status_code == 200
    assert client.post(BASE + f"campaigns/{campaign.pk}/complete/").status_code == 409
    assert client.post(BASE + "applications/", {"campaign": str(campaign.pk), "job": str(job.pk)}, format="json").status_code == 409
    assert client.get(BASE + "jobs/?company=not-a-uuid").status_code == 400
    assert client.get(BASE + "events/?campaign=not-a-uuid").status_code == 400


def test_unsupported_resource_methods_return_405_not_server_error(workspace):
    _, operator, _, _, candidate, campaign, _, job, _ = workspace
    client = api(operator)
    assert client.patch(BASE + "jobs/", {}, format="json").status_code == 405
    assert client.post(BASE + f"jobs/{job.pk}/", {}, format="json").status_code == 405
    assert client.patch(BASE + "admin/candidates/", {}, format="json").status_code == 405
    assert client.post(BASE + f"campaigns/{campaign.pk}/applications/", {}, format="json").status_code == 405


def test_database_rejects_duplicate_application_even_outside_api(workspace):
    *_, campaign, company, job, contact = workspace
    Application.objects.create(campaign=campaign, job=job)
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            Application.objects.create(campaign=campaign, job=job)


def test_same_candidate_cannot_apply_twice_across_campaigns(workspace):
    _, operator, _, _, candidate, campaign, _, job, _ = workspace
    Application.objects.create(campaign=campaign, job=job)
    another = Campaign.objects.create(candidate=candidate, plan="NORMAL_APPLY", status="ACTIVE", assigned_to=operator)
    result = api(operator).post(BASE + "applications/", {"campaign": str(another.pk), "job": str(job.pk)}, format="json")
    assert result.status_code == 409


def test_documented_application_flow_with_failure_retry_and_interview_date(workspace):
    owner, operator, _, _, _, campaign, _, job, _ = workspace
    client = api(operator)
    created = client.post(BASE + "applications/", {"campaign": str(campaign.pk), "job": str(job.pk)}, format="json")
    oid = created.json()["id"]
    route = BASE + f"applications/{oid}/transition/"
    for status in ("DISCOVERED", "SHORTLISTED", "QUEUED", "IN_PROGRESS"):
        assert client.post(route, {"status": status}, format="json").status_code == 200
    assert client.post(route, {"status": "APPLICATION_FAILED"}, format="json").status_code == 400
    failed = client.post(route, {"status": "APPLICATION_FAILED", "notes": "Manual portal requires candidate clarification"}, format="json")
    assert failed.status_code == 200
    assert failed.json()["failed_at"] and failed.json()["in_progress_at"]
    assert HumanTask.objects.filter(campaign=campaign, task_type="APPLICATION_FIT_REVIEW").count() == 1
    assert HumanTask.objects.filter(campaign=campaign, task_type="APPLICATION_FAILURE_REVIEW", priority=1).count() == 1
    for status in ("QUEUED", "IN_PROGRESS", "SUBMITTED", "IN_REVIEW", "RECRUITER_CONTACTED", "INTERVIEW"):
        assert client.post(route, {"status": status}, format="json").status_code == 200
    assert client.post(route, {"status": "INTERVIEW_SCHEDULED"}, format="json").status_code == 400
    assert client.post(route, {"status": "INTERVIEW_SCHEDULED", "interview_scheduled_at": "not-a-date"}, format="json").status_code == 400
    assert client.post(route, {"status": "INTERVIEW_SCHEDULED", "interview_scheduled_at": (timezone.now() - timedelta(days=1)).isoformat()}, format="json").status_code == 400
    date = (timezone.now() + timedelta(days=3)).replace(microsecond=0)
    scheduled = client.post(route, {"status": "INTERVIEW_SCHEDULED", "interview_scheduled_at": date.isoformat()}, format="json")
    assert scheduled.status_code == 200
    obj = Application.objects.get(pk=oid)
    assert obj.interview_scheduled_at == date
    visible = api(owner).get(BASE + f"applications/{oid}/").json()
    assert visible["interview_scheduled_at"]
    assert "failure_reason" not in visible
    assert HumanTask.objects.filter(campaign=campaign, task_type="INTERVIEW_CONFIRMATION", priority=1).count() == 1
    metrics = client.get(BASE + "dashboard/").json()
    assert metrics["applications"]["interviews"] == 1
    assert metrics["applications"]["interview_scheduled"] == 1
    assert metrics["applications"]["by_status"]["INTERVIEW_SCHEDULED"] == 1
    event = Event.objects.filter(event_type="applications.status_changed", payload__to="INTERVIEW_SCHEDULED").get()
    assert event.actor == operator
    assert event.payload["before"]["status"] == "INTERVIEW"
    assert event.payload["after"]["status"] == "INTERVIEW_SCHEDULED"
    assert "notes" not in event.payload and "failure_reason" not in event.payload


def test_interview_reschedule_and_transition_back_to_unscheduled(workspace):
    _, operator, _, _, _, campaign, _, job, _ = workspace
    future = timezone.now() + timedelta(days=5)
    obj = Application.objects.create(campaign=campaign, job=job, status="INTERVIEW_SCHEDULED", interview_scheduled_at=future)
    route = BASE + f"applications/{obj.pk}/"
    client = api(operator)
    assert client.patch(route, {"interview_scheduled_at": None}, format="json").status_code == 400
    assert client.patch(route, {"interview_scheduled_at": (timezone.now() - timedelta(days=1)).isoformat()}, format="json").status_code == 400
    assert client.patch(route, {"interview_scheduled_at": (future + timedelta(days=1)).isoformat()}, format="json").status_code == 200
    assert client.post(route + "transition/", {"status": "INTERVIEW"}, format="json").status_code == 200
    obj.refresh_from_db()
    assert obj.interview_scheduled_at is None


def test_documented_outreach_flow_delivery_negative_reply_and_audit(workspace):
    _, operator, _, _, _, campaign, _, _, contact = workspace
    client = api(operator)
    created = client.post(BASE + "outreach/", {"campaign": str(campaign.pk), "contact": str(contact.pk), "channel": "EMAIL", "body": "Reviewed message"}, format="json")
    oid = created.json()["id"]
    route = BASE + f"outreach/{oid}/transition/"
    for status in ("TARGET_IDENTIFIED", "CONTACT_VERIFIED", "DRAFTED", "REVIEW_REQUIRED", "SENT", "DELIVERED", "REPLIED", "NEGATIVE_REPLY"):
        result = client.post(route, {"status": status}, format="json")
        assert result.status_code == 200, result.data
    obj = Outreach.objects.get(pk=oid)
    assert obj.sent_at and obj.delivered_at and obj.reply_at
    assert HumanTask.objects.filter(campaign=campaign, task_type="CONTACT_VERIFICATION").count() == 1
    assert HumanTask.objects.filter(campaign=campaign, task_type="OUTREACH_REVIEW").count() == 1
    assert client.patch(BASE + f"outreach/{oid}/", {"body": "Cannot change sent text"}, format="json").status_code == 409
    metrics = client.get(BASE + "dashboard/").json()["outreach"]
    assert metrics["sent"] == metrics["delivered"] == 0
    assert metrics["replies"] == metrics["negative_replies"] == 1
    assert metrics["sent_lifetime"] == metrics["replied_lifetime"] == metrics["delivered_lifetime"] == 1
    assert metrics["by_status"]["NEGATIVE_REPLY"] == 1
    audit = Event.objects.filter(event_type="outreach.status_changed", payload__to="NEGATIVE_REPLY").get()
    assert audit.actor == operator
    assert audit.payload["before"]["status"] == "REPLIED"
    assert audit.payload["after"]["status"] == "NEGATIVE_REPLY"
    assert client.post(route, {"status": "SENT"}, format="json").status_code == 409


def test_outreach_bounce_requires_failure_notes_and_creates_review_task(workspace):
    _, operator, _, _, _, campaign, _, _, contact = workspace
    obj = Outreach.objects.create(campaign=campaign, contact=contact, status="SENT", body="Sent message", sent_at=timezone.now())
    client = api(operator)
    route = BASE + f"outreach/{obj.pk}/transition/"
    assert client.post(route, {"status": "BOUNCED"}, format="json").status_code == 400
    assert client.post(route, {"status": "BOUNCED", "notes": "Mailbox unavailable"}, format="json").status_code == 200
    obj.refresh_from_db()
    assert obj.bounced_at
    assert HumanTask.objects.filter(campaign=campaign, task_type="OUTREACH_FAILURE_REVIEW", priority=1).count() == 1


def test_failed_retry_reuses_open_task_and_unknown_states_are_rejected(workspace):
    _, operator, _, _, _, campaign, _, job, _ = workspace
    obj = Application.objects.create(campaign=campaign, job=job, status="IN_PROGRESS")
    client = api(operator)
    route = BASE + f"applications/{obj.pk}/transition/"
    for status in ("APPLICATION_FAILED", "QUEUED", "IN_PROGRESS", "APPLICATION_FAILED"):
        assert client.post(route, {"status": status, "notes": "Clarification required"}, format="json").status_code == 200
    assert HumanTask.objects.filter(campaign=campaign, task_type="APPLICATION_FAILURE_REVIEW").count() == 1
    assert client.post(route, {"status": "INVENTED"}, format="json").status_code == 409


def test_all_documented_states_have_a_metric_bucket(workspace):
    from apps.dashboard.selectors import campaign_metrics
    _, operator, _, _, _, campaign, _, _, _ = workspace
    metrics = campaign_metrics(operator)
    assert set(metrics["applications"]["by_status"]) == set(Application.Status.values)
    assert set(metrics["outreach"]["by_status"]) == set(Outreach.Status.values)
    assert metrics["applications"]["by_status"]["APPLICATION_FAILED"] == 0
    assert metrics["outreach"]["by_status"]["TARGET_IDENTIFIED"] == 0


@pytest.mark.parametrize("preparation", [None, "DISCOVERED", "SHORTLISTED"])
@pytest.mark.parametrize("outcome", ["REJECTED", "WITHDRAWN"])
def test_explicit_submission_updates_scoped_counts_and_preserves_evidence(workspace, preparation, outcome):
    owner, operator, admin, other, candidate, campaign, _, job, _ = workspace
    client = api(operator)
    created = client.post(BASE + "applications/", {"campaign": str(campaign.pk), "job": str(job.pk)}, format="json")
    assert created.status_code == 201
    data = created.json()
    assert data["status"] == "SAVED" and data["submitted_at"] is None
    assert data["candidate_id"] == candidate.pk
    assert data["candidate_name"] == candidate.full_name
    assert data["candidate_email"] == owner.email
    assert data["campaign_plan"] == campaign.plan
    assert data["campaign_status"] == "ACTIVE"
    route = BASE + f"applications/{data['id']}/transition/"
    if preparation:
        assert client.post(route, {"status": preparation}, format="json").status_code == 200

    def assert_counts(submitted):
        for identity in (owner, operator, admin):
            metrics = api(identity).get(BASE + "dashboard/").json()["applications"]
            assert metrics["total"] == 1 and metrics["submitted"] == submitted
        assert api(other).get(BASE + "dashboard/").json()["applications"]["submitted"] == 0
        for identity in (operator, admin):
            candidate_data = api(identity).get(BASE + f"admin/candidates/{candidate.pk}/").json()
            assert candidate_data["applications_submitted"] == submitted

    assert_counts(0)
    result = client.post(route, {"status": "SUBMITTED"}, format="json")
    assert result.status_code == 200, result.data
    timestamp = result.json()["submitted_at"]
    assert timestamp
    assert_counts(1)
    assert client.post(route, {"status": "SUBMITTED"}, format="json").status_code == 409
    result = client.post(route, {"status": outcome}, format="json")
    assert result.status_code == 200 and result.json()["submitted_at"] == timestamp
    assert_counts(1)
    customer_data = api(owner).get(BASE + f"applications/{data['id']}/").json()
    assert customer_data["status"] == outcome
    assert not {"candidate_id", "candidate_name", "candidate_email"} & customer_data.keys()


@pytest.mark.parametrize("field,value", [
    ("candidate", 999), ("candidate_id", 999), ("candidate_name", "Spoof"),
    ("candidate_email", "spoof@example.com"), ("campaign_plan", "NORMAL_APPLY"),
    ("campaign_status", "ACTIVE"), ("status", "SUBMITTED"),
    ("submitted_at", "2026-01-01T00:00:00Z"),
])
def test_application_identity_and_submission_fields_cannot_be_spoofed(workspace, field, value):
    _, operator, _, _, candidate, campaign, _, job, _ = workspace
    client = api(operator)
    payload = {"campaign": str(campaign.pk), "job": str(job.pk)}
    assert client.post(BASE + "applications/", {**payload, field: value}, format="json").status_code == 400
    assert not Application.objects.exists()
    created = client.post(BASE + "applications/", payload, format="json").json()
    route = BASE + f"applications/{created['id']}/"
    assert client.patch(route, {field: value}, format="json").status_code == 400
    if field != "status":
        assert client.post(route + "transition/", {"status": "SUBMITTED", field: value}, format="json").status_code == 400
    obj = Application.objects.get(pk=created["id"])
    assert obj.candidate_id == candidate.pk
    assert obj.status == "SAVED" and obj.submitted_at is None


@pytest.mark.parametrize("blocker", ["DRAFT", "ONBOARDING", "READY", "PAUSED", "COMPLETED", "CANCELLED", "CLOSED"])
def test_explicit_submission_respects_existing_campaign_and_job_guards(workspace, blocker):
    _, operator, _, _, _, campaign, _, job, _ = workspace
    obj = Application.objects.create(campaign=campaign, job=job)
    if blocker == "CLOSED":
        job.status = blocker
        job.save()
    else:
        campaign.status = blocker
        campaign.save()
    result = api(operator).post(BASE + f"applications/{obj.pk}/transition/", {"status": "SUBMITTED"}, format="json")
    assert result.status_code == 409
    obj.refresh_from_db()
    assert obj.status == "SAVED" and obj.submitted_at is None
    assert not Event.objects.filter(event_type="applications.status_changed").exists()


@pytest.mark.parametrize("plan", ["NORMAL_APPLY", "COLD_APPLY", "FULL_THROTTLE"])
def test_current_marketed_plans_can_record_confirmed_submissions(workspace, plan):
    owner, operator, _, _, candidate, campaign, _, job, _ = workspace
    campaign.plan = plan
    campaign.save()
    obj = Application.objects.create(campaign=campaign, job=job)
    response = api(operator).post(BASE + f"applications/{obj.pk}/transition/", {"status": "SUBMITTED"}, format="json")
    assert response.status_code == 200
    obj.refresh_from_db()
    assert obj.submitted_at is not None and obj.status == "SUBMITTED"
    assert api(owner).get(BASE + "dashboard/").json()["applications"]["submitted"] == 1
    assert api(operator).get(BASE + f"admin/candidates/{candidate.pk}/").json()["applications_submitted"] == 1


def test_submission_visibility_and_campaign_readiness_cannot_be_bypassed(workspace):
    owner, operator, _, other, _, campaign, _, job, _ = workspace
    obj = Application.objects.create(campaign=campaign, job=job)
    route = BASE + f"applications/{obj.pk}/transition/"
    assert api(owner).post(route, {"status": "SUBMITTED"}, format="json").status_code == 403
    assert api(other).post(route, {"status": "SUBMITTED"}, format="json").status_code == 404
    outsider = user("submission-outsider")
    assert api(outsider).get(BASE + f"applications/{obj.pk}/").status_code == 404
    assert api(outsider).get(BASE + "applications/", {"campaign": str(campaign.pk)}).status_code == 404
    assert api(other).get(BASE + "applications/", {"campaign": str(campaign.pk)}).status_code == 404
    campaign.status = "DRAFT"
    campaign.save()
    assert api(operator).post(BASE + f"campaigns/{campaign.pk}/start/").status_code == 409
    assert api(operator).post(route, {"status": "SUBMITTED"}, format="json").status_code == 409
    obj.refresh_from_db()
    assert obj.status == "SAVED" and obj.submitted_at is None


def test_application_identity_serialization_uses_eager_loaded_actual_candidate(workspace, django_assert_num_queries):
    from apps.operations.selectors import records
    from apps.operations.serializers import ApplicationSerializer
    from types import SimpleNamespace

    owner, operator, _, _, candidate, campaign, company, job, _ = workspace
    Application.objects.create(campaign=campaign, job=job)
    second_job = Job.objects.create(company=company, title="Second", identity_key="identity-second")
    Application.objects.create(campaign=campaign, job=second_job)
    objects = list(records(operator, "applications"))
    with django_assert_num_queries(0):
        data = ApplicationSerializer(objects, many=True, context={"request": SimpleNamespace(user=operator)}).data
    assert all(row["candidate_id"] == candidate.pk and row["candidate_email"] == owner.email for row in data)
