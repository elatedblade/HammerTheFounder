from unittest.mock import Mock
import pytest
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIClient
from apps.users.models import User
from apps.candidates.models import CandidateProfile
from apps.campaigns.models import Campaign
from apps.companies.models import Company
from apps.contacts.models import Contact
from apps.jobs.models import Job
from apps.outreach.models import Suppression
from apps.resumes.models import Resume
from apps.ai.models import AIRun
from apps.ai.inputs import validate_input, canonical_input
from apps.ai.services import create_run, execute_run
from apps.integrations.ai.omniroute import GatewayError
from apps.notifications.services import create_notification, dispatch_notification

pytestmark = pytest.mark.django_db


@pytest.fixture
def canonical_world(monkeypatch):
    client = User.objects.create_user("clerk", "canonical-client", email="client@example.com", phone="+919999999999")
    operator = User.objects.create_user("clerk", "canonical-operator", email="operator@example.com", role="OPERATOR")
    profile = CandidateProfile.objects.create(user=client, full_name="Canonical Candidate", headline="Engineer", target_roles=["Backend Engineer"])
    campaign = Campaign.objects.create(candidate=profile, plan="NORMAL_APPLY", assigned_to=operator)
    company = Company.objects.create(name="Canonical Company", identity_key="canonical-company")
    job = Job.objects.create(company=company, title="Canonical Job", description="Canonical description", identity_key="canonical-job")
    contact = Contact.objects.create(company=company, name="Canonical Contact", email="contact@example.com", identity_key="canonical-contact")
    monkeypatch.setattr("apps.ai.services.configuration", lambda: {"OMNIROUTE_MODEL": "configured-model"})
    monkeypatch.setattr("apps.ai.services.enqueue_run", Mock())
    return client, operator, profile, campaign, job, contact


@pytest.mark.parametrize("capability,input_data", [
    ("profile_extract", {"resume_text": "forged raw resume"}),
    ("job_match", {"job_id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa", "profile": {"full_name": "Forged"}}),
    ("outreach_draft", {"contact_id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa", "candidate": "Forged"}),
    ("qa", {"content": "Review draft", "resume": "Forged"}),
])
def test_inputs_reject_raw_candidate_overrides(capability, input_data):
    with pytest.raises(ValidationError):
        validate_input(capability, input_data)


def test_job_match_loads_job_company_and_profile(canonical_world):
    _, _, profile, campaign, job, _ = canonical_world
    payload, refs = canonical_input(campaign, "job_match", {"job_id": str(job.pk)})
    assert payload["candidate"]["full_name"] == profile.full_name
    assert payload["job"]["title"] == "Canonical Job"
    assert payload["company"]["name"] == "Canonical Company"
    assert refs["job"]["id"] == str(job.pk)
    assert "full_name" not in refs["candidate"]


def test_run_stores_references_not_profile_and_reloads_latest_facts(canonical_world, monkeypatch):
    _, operator, profile, campaign, job, _ = canonical_world
    run = create_run(user=operator, data={"campaign": campaign.pk, "capability": "job_match", "input": {"job_id": str(job.pk)}})
    assert run.input_json == {"job_id": str(job.pk)}
    assert run.agent_version and run.prompt_version and run.source_references["candidate"]["id"] == profile.pk
    profile.full_name = "Updated canonical candidate"
    profile.profile_version += 1
    profile.save()
    generation = Mock(return_value=({"score": 70, "reasons": [], "gaps": []}, {"model": "configured-model", "request_id": "req", "usage": {}}))
    monkeypatch.setattr("apps.ai.services.generate", generation)
    execute_run(run.pk)
    assert generation.call_args.kwargs["input_data"]["candidate"]["full_name"] == "Updated canonical candidate"
    run.refresh_from_db()
    assert run.source_references["candidate"]["profile_version"] == profile.profile_version
    assert run.input_json == {"job_id": str(job.pk)}


def test_profile_extract_requires_parsed_campaign_owned_resume(canonical_world):
    client, operator, profile, campaign, _, _ = canonical_world
    other_user = User.objects.create_user("clerk", "canonical-other", email="other@example.com")
    other_profile = CandidateProfile.objects.create(user=other_user)
    resume = Resume.objects.create(candidate=other_profile, s3_key="other/resume", original_filename="cv.pdf", content_type="application/pdf", file_size=100, upload_status="UPLOADED", parse_status="PARSED", extracted_text="Private other candidate")
    data = {"campaign": campaign.pk, "capability": "profile_extract", "input": {"resume_id": str(resume.pk)}}
    with pytest.raises(ValidationError):
        create_run(user=operator, data=data)
    resume.candidate = profile
    resume.parse_status = "PROCESSING"
    resume.save()
    with pytest.raises(ValidationError):
        create_run(user=operator, data=data)
    resume.parse_status = "PARSED"
    resume.save()
    run = create_run(user=operator, data=data)
    assert run.input_json == {"resume_id": str(resume.pk)}


def test_outreach_reads_contact_company_and_blocks_suppression(canonical_world):
    _, operator, _, campaign, _, contact = canonical_world
    payload, _ = canonical_input(campaign, "outreach_draft", {"contact_id": str(contact.pk)})
    assert payload["contact"]["name"] == "Canonical Contact"
    assert payload["suppression"]["suppressed"] is False
    Suppression.objects.create(email="CONTACT@example.com", reason="Do not contact")
    with pytest.raises(ValidationError):
        create_run(user=operator, data={"campaign": campaign.pk, "capability": "outreach_draft", "input": {"contact_id": str(contact.pk)}})


def test_suppression_added_after_enqueue_prevents_model_request(canonical_world, monkeypatch):
    _, operator, _, campaign, _, contact = canonical_world
    run = create_run(user=operator, data={"campaign": campaign.pk, "capability": "outreach_draft", "input": {"contact_id": str(contact.pk)}})
    Suppression.objects.create(email=contact.email, reason="Do not contact")
    generation = Mock()
    monkeypatch.setattr("apps.ai.services.generate", generation)
    execute_run(run.pk)
    generation.assert_not_called()
    run.refresh_from_db()
    assert run.status == "FAILED" and run.error_code == "contact_suppressed"


def test_qa_uses_content_and_canonical_facts(canonical_world):
    _, _, profile, campaign, _, _ = canonical_world
    payload, _ = canonical_input(campaign, "qa", {"content": "Review this claim"})
    assert payload["content_for_review"] == "Review this claim"
    assert payload["candidate"]["full_name"] == profile.full_name


def test_deactivated_operator_cannot_execute_queued_run(canonical_world, monkeypatch):
    _, operator, _, campaign, job, _ = canonical_world
    run = create_run(user=operator, data={"campaign": campaign.pk, "capability": "job_match", "input": {"job_id": str(job.pk)}})
    operator.is_active = False
    operator.save()
    generation = Mock()
    monkeypatch.setattr("apps.ai.services.generate", generation)
    execute_run(run.pk)
    generation.assert_not_called()
    run.refresh_from_db()
    assert run.status == "FAILED"


def test_parsed_text_operational_scoped_bounded_and_client_denied(canonical_world):
    client, operator, profile, _, _, _ = canonical_world
    resume = Resume.objects.create(candidate=profile, s3_key="owned/resume", original_filename="cv.pdf", content_type="application/pdf", file_size=100, upload_status="UPLOADED", parse_status="PARSED", extracted_text="x" * 40000)
    api = APIClient()
    api.force_authenticate(operator)
    response = api.get(f"/api/v1/resumes/{resume.pk}/parsed-text/")
    assert response.status_code == 200 and len(response.json()["text"]) == 32000 and response.json()["truncated"] is True
    assert "no-store" in response["Cache-Control"]
    api.force_authenticate(client)
    assert api.get(f"/api/v1/resumes/{resume.pk}/parsed-text/").status_code == 403
    stranger = User.objects.create_user("clerk", "canonical-stranger-operator", email="stranger@example.com", role="OPERATOR")
    api.force_authenticate(stranger)
    assert api.get(f"/api/v1/resumes/{resume.pk}/parsed-text/").status_code == 404


def test_whatsapp_requires_saved_customer_phone_and_current_match(canonical_world):
    client, operator, _, campaign, _, _ = canonical_world
    data = {"campaign": campaign.pk, "channel": "WHATSAPP", "recipient": "+918888888888", "body": "Update"}
    with pytest.raises(ValidationError):
        create_notification(user=operator, data=data)
    item = create_notification(user=operator, data={**data, "recipient": "+91 99999 99999"})
    client.phone = ""
    client.save()
    with pytest.raises(ValidationError):
        dispatch_notification(user=operator, notification_id=item.pk, manual=True)
    with pytest.raises(ValidationError):
        create_notification(user=operator, data={**data, "recipient": "+919999999999"})
