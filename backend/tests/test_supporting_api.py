from unittest.mock import Mock

import pytest
from rest_framework.test import APIClient
from apps.users.models import User
from apps.candidates.models import CandidateProfile
from apps.campaigns.models import Campaign
from apps.billing.models import Payment
from apps.notifications.models import Notification
from apps.ai.models import AIRun
from apps.resumes.models import Resume

pytestmark = pytest.mark.django_db


@pytest.fixture
def world():
    owner = User.objects.create_user("clerk", "support-api-owner", email="owner@example.com")
    outsider = User.objects.create_user("clerk", "support-api-outsider", email="outsider@example.com")
    admin = User.objects.create_user("clerk", "support-api-admin", email="admin@example.com", role="ADMIN")
    operator = User.objects.create_user("clerk", "support-api-operator", email="operator@example.com", role="OPERATOR")
    profile = CandidateProfile.objects.create(user=owner)
    campaign = Campaign.objects.create(candidate=profile, plan="NORMAL_APPLY", assigned_to=admin)
    return owner, outsider, admin, operator, profile, campaign


def api(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


def test_client_payment_list_is_scoped_and_sanitized(world):
    owner, outsider, _, _, _, campaign = world
    Payment.objects.create(campaign=campaign, amount="125.00", notes="private internal note", reference="bank-reference")
    response = api(owner).get("/api/v1/billing/payments/")
    assert response.status_code == 200
    assert response.json()[0]["amount"] == "125.00"
    assert not {"notes", "reference", "verified_by"} & response.json()[0].keys()
    assert api(outsider).get("/api/v1/billing/payments/").json() == []


def test_unconfigured_upi_is_honest(world, settings):
    settings.UPI_ID = ""
    settings.UPI_PAYEE_NAME = ""
    settings.UPI_INSTRUCTIONS = ""
    response = api(world[0]).get("/api/v1/billing/instructions/")
    assert response.json() == {"configured": False, "upi_id": "", "payee_name": "", "instructions": ""}


def test_client_cannot_create_payment_or_ai_run(world):
    owner, _, _, _, _, campaign = world
    payload = {"campaign": str(campaign.pk), "amount": "100.00"}
    assert api(owner).post("/api/v1/billing/payments/", payload, format="json").status_code == 403
    assert api(owner).post("/api/v1/ai/runs/", {}, format="json").status_code == 403


def test_notifications_hide_drafts_from_customer(world):
    owner, outsider, admin, _, _, campaign = world
    Notification.objects.create(campaign=campaign, channel="WHATSAPP", recipient="phone", body="draft private text", created_by=admin)
    sent = Notification.objects.create(campaign=campaign, channel="WHATSAPP", recipient="phone", body="sent update", created_by=admin, status="SENT")
    assert [item["id"] for item in api(owner).get("/api/v1/notifications/").json()] == [str(sent.pk)]
    assert api(outsider).get("/api/v1/notifications/").json() == []


def test_ai_run_scope_and_missing_configuration(world, settings):
    _, _, admin, operator, _, campaign = world
    run = AIRun.objects.create(campaign=campaign, capability="qa", created_by=admin)
    assert api(operator).get(f"/api/v1/ai/runs/{run.pk}/").status_code == 404
    settings.OMNIROUTE_BASE_URL = ""
    settings.OMNIROUTE_API_KEY = ""
    settings.OMNIROUTE_MODEL = ""
    response = api(admin).post("/api/v1/ai/runs/", {"campaign": str(campaign.pk), "capability": "qa", "input": {}}, format="json")
    assert response.status_code == 503 and response.json()["code"] == "AI_NOT_CONFIGURED"


def test_resume_download_and_candidate_metadata_scope(world, monkeypatch):
    owner, outsider, admin, operator, profile, _ = world
    item = Resume.objects.create(candidate=profile, s3_key="private/storage/key", original_filename="cv.pdf", content_type="application/pdf", file_size=200, upload_status="UPLOADED")
    storage = Mock()
    storage.authorize_download.return_value = "https://example.test/private-signed"
    monkeypatch.setattr("apps.resumes.processing.get_resume_storage", lambda: storage)
    url = f"/api/v1/resumes/{item.pk}/download/"
    assert api(outsider).post(url).status_code == 404
    assert api(operator).post(url).status_code == 404
    response = api(owner).post(url)
    assert response.status_code == 200 and "no-store" in response["Cache-Control"]
    metadata = api(admin).get(f"/api/v1/admin/candidates/{profile.pk}/resumes/").json()[0]
    assert "s3_key" not in metadata and "extracted_text" not in metadata
    assert api(operator).get(f"/api/v1/admin/candidates/{profile.pk}/resumes/").status_code == 404


def test_inactive_identity_cannot_access_supporting_routes(world):
    owner = world[0]
    owner.is_active = False
    owner.save()
    for route in ("billing/payments/", "billing/instructions/", "notifications/", "ai/runs/"):
        assert api(owner).get("/api/v1/" + route).status_code == 403
