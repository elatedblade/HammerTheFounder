from datetime import timedelta
from decimal import Decimal
from io import BytesIO
from unittest.mock import Mock
from zipfile import ZipFile

import pytest
from django.http import Http404
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.test import APIClient

from apps.users.models import User
from apps.candidates.models import CandidateProfile
from apps.campaigns.models import Campaign
from apps.billing.models import Payment
from apps.billing.services import create_payment, transition_payment, Conflict
from apps.billing.trials import expire_trials
from apps.notifications.models import Notification
from apps.notifications.services import create_notification, dispatch_notification, deliver_notification
from apps.integrations.email.resend import EmailDeliveryError
from apps.ai.models import AIRun
from apps.ai.services import create_run, execute_run
from apps.integrations.ai.omniroute import AINotConfigured, GatewayError
from apps.resumes.models import Resume
from apps.resumes.parsing import extract_text, DocumentParseError
from apps.resumes.processing import download_resume, queue_parse, process_resume

pytestmark = pytest.mark.django_db


@pytest.fixture
def records():
    client = User.objects.create_user("clerk", "support-client", email="client@example.com", phone="+919999999999")
    admin = User.objects.create_user("clerk", "support-admin", email="admin@example.com", role="ADMIN")
    operator = User.objects.create_user("clerk", "support-operator", email="operator@example.com", role="OPERATOR")
    profile = CandidateProfile.objects.create(user=client)
    campaign = Campaign.objects.create(candidate=profile, plan="NORMAL_APPLY", assigned_to=operator)
    return client, admin, operator, profile, campaign


def payment_data(campaign):
    return {"campaign": campaign.pk, "amount": Decimal("100.00"), "currency": "INR"}


def test_payment_creation_idempotency_and_conflict(records):
    _, admin, _, _, campaign = records
    first, created = create_payment(user=admin, data=payment_data(campaign), key="receipt-1")
    second, created_again = create_payment(user=admin, data=payment_data(campaign), key="receipt-1")
    assert first.pk == second.pk and created and not created_again
    with pytest.raises(Conflict):
        create_payment(user=admin, data={**payment_data(campaign), "amount": Decimal("200")}, key="receipt-1")


def test_payment_verify_and_refund_update_campaign(records):
    _, admin, _, _, campaign = records
    payment, _ = create_payment(user=admin, data=payment_data(campaign))
    transition_payment(user=admin, payment_id=payment.pk, target="VERIFIED", reference="UPI-123")
    campaign.refresh_from_db()
    assert campaign.billing_status == "ACTIVE"
    version = campaign.version
    transition_payment(user=admin, payment_id=payment.pk, target="VERIFIED", reference="UPI-123")
    campaign.refresh_from_db()
    assert campaign.version == version
    transition_payment(user=admin, payment_id=payment.pk, target="REFUNDED")
    campaign.refresh_from_db()
    assert campaign.billing_status == "PENDING"


def test_reference_cannot_be_reused(records):
    _, admin, _, _, campaign = records
    one, _ = create_payment(user=admin, data=payment_data(campaign))
    two, _ = create_payment(user=admin, data=payment_data(campaign))
    transition_payment(user=admin, payment_id=one.pk, target="VERIFIED", reference="unique-ref")
    with pytest.raises(Conflict):
        transition_payment(user=admin, payment_id=two.pk, target="VERIFIED", reference="unique-ref")
    two.refresh_from_db()
    assert two.status == "PENDING"


def test_operator_cannot_verify_and_client_cannot_create(records):
    client, admin, operator, _, campaign = records
    payment, _ = create_payment(user=admin, data=payment_data(campaign))
    with pytest.raises(PermissionDenied):
        transition_payment(user=operator, payment_id=payment.pk, target="VERIFIED", reference="x")
    with pytest.raises(PermissionDenied):
        create_payment(user=client, data=payment_data(campaign))


def test_operator_payment_scope_denied(records):
    _, _, operator, _, campaign = records
    campaign.assigned_to = None
    campaign.status = "ACTIVE"
    campaign.save()
    with pytest.raises(Http404):
        create_payment(user=operator, data=payment_data(campaign))


def test_trial_expiry_idempotent_and_paid_campaign_untouched(records):
    _, _, _, _, campaign = records
    campaign.status = "ACTIVE"
    campaign.trial_end_date = timezone.localdate() - timedelta(days=1)
    campaign.save()
    assert expire_trials() == 1
    assert expire_trials() == 0
    campaign.refresh_from_db()
    assert campaign.status == "PAUSED" and campaign.billing_status == "PAST_DUE"
    campaign.status = "ACTIVE"
    campaign.billing_status = "ACTIVE"
    campaign.save()
    assert expire_trials() == 0


def notification_data(campaign, channel="EMAIL"):
    return {"campaign": campaign.pk, "channel": channel, "recipient": "client@example.com" if channel == "EMAIL" else "+919999999999", "subject": "Campaign update", "body": "Your update"}


def test_transactional_email_rejects_cold_recipient(records):
    _, admin, _, _, campaign = records
    with pytest.raises(ValidationError):
        create_notification(user=admin, data={**notification_data(campaign), "recipient": "lead@example.com"})
    assert Notification.objects.count() == 0


def test_whatsapp_manual_mark_is_idempotent(records):
    _, admin, _, _, campaign = records
    item = create_notification(user=admin, data=notification_data(campaign, "WHATSAPP"))
    first = dispatch_notification(user=admin, notification_id=item.pk, manual=True)
    again = dispatch_notification(user=admin, notification_id=item.pk, manual=True)
    assert first.sent_at == again.sent_at and again.status == "SENT"


def test_queued_email_delivery_and_duplicate_task_do_not_resend(records, monkeypatch):
    _, admin, _, _, campaign = records
    item = create_notification(user=admin, data=notification_data(campaign))
    item.status = "QUEUED"
    item.save()
    delivery = Mock(return_value="resend-id")
    monkeypatch.setattr("apps.notifications.services.deliver", delivery)
    deliver_notification(item.pk)
    deliver_notification(item.pk)
    item.refresh_from_db()
    assert item.status == "SENT" and item.provider_id == "resend-id"
    assert delivery.call_count == 1


def test_email_retry_is_bounded_and_idempotency_key_stable(records, monkeypatch):
    _, admin, _, _, campaign = records
    item = create_notification(user=admin, data=notification_data(campaign))
    item.status = "QUEUED"
    item.save()
    delivery = Mock(side_effect=EmailDeliveryError("provider_unavailable", True))
    monkeypatch.setattr("apps.notifications.services.deliver", delivery)
    for _ in range(2):
        with pytest.raises(EmailDeliveryError):
            deliver_notification(item.pk)
    deliver_notification(item.pk)
    item.refresh_from_db()
    assert item.status == "UNKNOWN" and item.attempts == 3
    assert len({call.kwargs["idempotency_key"] for call in delivery.call_args_list}) == 1


def test_ai_unconfigured_does_not_create_run(records, settings):
    _, admin, _, _, campaign = records
    settings.OMNIROUTE_BASE_URL = ""
    settings.OMNIROUTE_API_KEY = ""
    settings.OMNIROUTE_MODEL = ""
    with pytest.raises(AINotConfigured):
        create_run(user=admin, data={"campaign": campaign.pk, "capability": "qa", "input": {}})
    assert AIRun.objects.count() == 0


def test_ai_result_is_proposal_only_and_task_idempotent(records, monkeypatch):
    _, admin, _, _, campaign = records
    run = AIRun.objects.create(campaign=campaign, created_by=admin, capability="qa", input_json={"content": "Review this draft"})
    generation = Mock(return_value=({"passed": True, "issues": [], "recommendations": []}, {"model": "configured-model", "request_id": "req", "usage": {"total_tokens": 5}}))
    monkeypatch.setattr("apps.ai.services.generate", generation)
    execute_run(run.pk)
    execute_run(run.pk)
    run.refresh_from_db()
    assert run.status == "SUCCEEDED" and run.result["requires_human_review"] is True
    assert run.usage_json == {"total_tokens": 5} and generation.call_count == 1
    campaign.refresh_from_db()
    assert campaign.status == "DRAFT"


def test_ai_failure_has_safe_code_not_raw_input(records, monkeypatch):
    _, admin, _, _, campaign = records
    run = AIRun.objects.create(campaign=campaign, created_by=admin, capability="qa", input_json={"content": "secret draft"})
    monkeypatch.setattr("apps.ai.services.generate", Mock(side_effect=GatewayError("invalid_model_output")))
    execute_run(run.pk)
    run.refresh_from_db()
    assert run.status == "FAILED" and run.error_code == "invalid_model_output" and run.result is None


def make_resume(profile, content_type="application/pdf"):
    return Resume.objects.create(candidate=profile, s3_key="private/resume", original_filename="resume.pdf", content_type=content_type, file_size=100, upload_status="UPLOADED")


def test_resume_download_ownership_and_pending_block(records, monkeypatch):
    client, _, _, profile, _ = records
    item = make_resume(profile)
    storage = Mock()
    storage.authorize_download.return_value = "https://signed.example.test/resume"
    monkeypatch.setattr("apps.resumes.processing.get_resume_storage", lambda: storage)
    assert download_resume(user=client, pk=item.pk)["expires_in"] == 300
    stranger = User.objects.create_user("clerk", "stranger", email="stranger@example.com")
    with pytest.raises(Http404):
        download_resume(user=stranger, pk=item.pk)
    item.upload_status = "PENDING_UPLOAD"
    item.save()
    with pytest.raises(Conflict):
        download_resume(user=client, pk=item.pk)


def test_legacy_doc_records_honest_unsupported_state(records, monkeypatch):
    _, admin, _, profile, _ = records
    item = make_resume(profile, "application/msword")
    monkeypatch.setattr("apps.resumes.processing.get_resume_storage", Mock())
    result = queue_parse(user=admin, pk=item.pk)
    assert result.parse_status == "UNSUPPORTED" and result.parse_error_code == "legacy_doc_not_supported"


def docx_bytes(xml):
    buffer = BytesIO()
    with ZipFile(buffer, "w") as archive:
        archive.writestr("word/document.xml", xml)
    return buffer.getvalue()


def test_docx_extraction_and_entity_rejection():
    content_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    xml = '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body><w:p><w:r><w:t>Engineer</w:t></w:r></w:p></w:body></w:document>'
    assert extract_text(docx_bytes(xml), content_type) == "Engineer"
    with pytest.raises(DocumentParseError) as error:
        extract_text(docx_bytes('<!DOCTYPE x [<!ENTITY e "bad">]><x>&e;</x>'), content_type)
    assert error.value.code == "unsafe_document"


def test_resume_task_does_not_repeat_successful_extraction(records, monkeypatch):
    _, _, _, profile, _ = records
    item = make_resume(profile)
    item.parse_status = "QUEUED"
    item.save()
    storage = Mock()
    storage.read_document.return_value = b"pdf test bytes"
    monkeypatch.setattr("apps.resumes.processing.get_resume_storage", lambda: storage)
    monkeypatch.setattr("apps.resumes.processing.extract_text", lambda *_: "Engineer")
    process_resume(item.pk)
    process_resume(item.pk)
    item.refresh_from_db()
    assert item.parse_status == "PARSED" and item.extracted_text == "Engineer"
    assert storage.read_document.call_count == 1
