"""Admin mutations must be readable by their customer, never other customers.

Runs in pytest's isolated database. No real accounts or external sends.
"""
import pytest
from rest_framework.test import APIClient
from apps.users.models import User
from apps.candidates.models import CandidateProfile
from apps.campaigns.models import Campaign

pytestmark = pytest.mark.django_db
BASE = "/api/v1/"


def api(user):
    client = APIClient()
    client.force_authenticate(user)
    return client


@pytest.fixture
def world():
    def user(name, role="CLIENT"):
        return User.objects.create_user("clerk", name, email=f"{name}@example.com", phone="15555550123", role=role)
    owner, outsider, admin, operator = user("sync-owner"), user("sync-outsider"), user("sync-admin", "ADMIN"), user("sync-operator", "OPERATOR")
    candidate = CandidateProfile.objects.create(user=owner, full_name="Synthetic sync candidate")
    campaign = Campaign.objects.create(candidate=candidate, plan="NORMAL_APPLY", status="ACTIVE", assigned_to=admin)
    return owner, outsider, admin, operator, candidate, campaign


def test_admin_application_updates_drive_customer_cards_history_and_counts(world):
    owner, outsider, admin, operator, candidate, campaign = world
    admin_api, customer = api(admin), api(owner)
    company = admin_api.post(BASE + "companies/", {"name": "Sync fixture company"}, format="json")
    assert company.status_code == 201
    job = admin_api.post(BASE + "jobs/", {"company": company.data["id"], "title": "Engineer", "status": "OPEN"}, format="json")
    assert job.status_code == 201
    created = admin_api.post(BASE + "applications/", {"campaign": str(campaign.pk), "job": job.data["id"], "notes": "Private operator note", "source_reference": "private-proof"}, format="json")
    assert created.status_code == 201
    url = BASE + f"applications/{created.data['id']}/transition/"
    for status, metric in [("READY", None), ("IN_PROGRESS", "in_progress"), ("SUBMITTED", "submitted"), ("IN_REVIEW", "in_review"), ("INTERVIEW", "interviews"), ("OFFER", "offers")]:
        changed = admin_api.post(url, {"status": status}, format="json")
        assert changed.status_code == 200, changed.data
        history = customer.get(BASE + "applications/").json()
        assert len(history) == 1 and history[0]["status"] == status
        assert not {"notes", "source_reference", "failure_reason"}.intersection(history[0])
        metrics = customer.get(BASE + "dashboard/").json()["applications"]
        assert metrics["total"] == 1
        if metric:
            assert metrics[metric] == 1
        assert api(outsider).get(BASE + "applications/", {"campaign": str(campaign.pk)}).status_code == 404
        assert api(operator).post(url, {"status": "WITHDRAWN"}, format="json").status_code == 404
        assert customer.post(url, {"status": "WITHDRAWN"}, format="json").status_code == 403
    counts = admin_api.get(BASE + f"admin/candidates/{candidate.pk}/").json()
    assert counts["applications_submitted"] == 1
    final_metrics = customer.get(BASE + "dashboard/").json()["applications"]
    assert final_metrics["in_progress"] == final_metrics["in_review"] == final_metrics["interviews"] == 0
    assert final_metrics["offers"] == 1


def test_admin_payment_verification_and_refund_are_customer_visible_without_private_fields(world):
    owner, outsider, admin, operator, candidate, campaign = world
    created = api(admin).post(BASE + "billing/payments/", {"campaign": str(campaign.pk), "amount": "125.00", "currency": "INR", "notes": "private billing note"}, format="json")
    assert created.status_code == 201
    payment = created.data["id"]
    for action, body, expected in [("verify", {"reference": "SYNC-RECEIPT-ONLY-TEST"}, "VERIFIED"), ("transition", {"status": "REFUNDED"}, "REFUNDED")]:
        url = BASE + f"billing/payments/{payment}/{action}/"
        assert api(owner).post(url, body, format="json").status_code == 403
        assert api(operator).post(url, body, format="json").status_code == 403
        assert api(admin).post(url, body, format="json").status_code == 200
        rows = api(owner).get(BASE + "billing/payments/", {"candidate": candidate.pk}).json()
        assert len(rows) == 1 and rows[0]["status"] == expected and rows[0]["amount"] == "125.00"
        assert not {"notes", "reference", "verified_by"}.intersection(rows[0])
        assert api(outsider).get(BASE + "billing/payments/", {"candidate": candidate.pk}).json() == []


def test_notification_draft_hidden_until_manual_send_recorded_and_inquiries_owned(world, settings):
    owner, outsider, admin, operator, candidate, campaign = world
    settings.WHATSAPP_BUSINESS_NUMBER = "15555550123"
    inquiry = api(owner).post(BASE + "candidate/inquiries/", {"plan": "NORMAL_APPLY"}, format="json")
    assert inquiry.status_code == 201
    inquiry_url = BASE + f"admin/inquiries/{inquiry.data['id']}/"
    assert api(admin).patch(inquiry_url, {"status": "CONTACTED", "notes": "private inquiry note"}, format="json").status_code == 200
    owned = api(owner).get(BASE + "candidate/inquiries/").json()
    assert owned[0]["status"] == "CONTACTED" and "notes" not in owned[0]
    assert api(outsider).get(BASE + "candidate/inquiries/").json() == []
    draft = api(admin).post(BASE + "notifications/", {"campaign": str(campaign.pk), "channel": "WHATSAPP", "recipient": owner.phone, "body": "Synthetic campaign update"}, format="json")
    assert draft.status_code == 201
    assert api(owner).get(BASE + "notifications/").json() == []
    send_url = BASE + f"notifications/{draft.data['id']}/mark-sent/"
    assert api(owner).post(send_url, {}, format="json").status_code == 403
    assert api(operator).post(send_url, {}, format="json").status_code == 404
    assert api(admin).post(send_url, {}, format="json").status_code == 200
    delivered = api(owner).get(BASE + "notifications/").json()
    assert len(delivered) == 1 and delivered[0]["status"] == "SENT"
    assert delivered[0]["body"] == "Synthetic campaign update"
    assert api(outsider).get(BASE + "notifications/").json() == []


def test_notifications_beyond_200_are_reachable_and_drafts_remain_private(world):
    from apps.notifications.models import Notification
    owner, outsider, admin, operator, candidate, campaign = world
    Notification.objects.bulk_create([
        Notification(campaign=campaign, created_by=admin, channel="WHATSAPP", recipient=owner.phone, body=f"Synthetic history {index}", status="SENT")
        for index in range(205)
    ])
    Notification.objects.create(campaign=campaign, created_by=admin, channel="WHATSAPP", recipient=owner.phone, body="private draft")
    first = api(owner).get(BASE + "notifications/", {"limit": 200})
    second = api(owner).get(BASE + "notifications/", {"limit": 200, "offset": 200})
    assert len(first.json()) == 200 and len(second.json()) == 5
    assert not {row["id"] for row in first.json()}.intersection(row["id"] for row in second.json())
    assert all(row["status"] == "SENT" for row in first.json() + second.json())
    assert "no-store" in first["Cache-Control"]
    assert api(outsider).get(BASE + "notifications/").json() == []


def test_admin_outreach_updates_are_visible_to_customer_without_internal_content(world):
    from apps.contacts.models import Contact
    from apps.outreach.models import Outreach
    owner, outsider, admin, operator, candidate, campaign = world
    company = api(admin).post(BASE + "companies/", {"name": "Outreach sync company"}, format="json")
    assert company.status_code == 201
    contact = api(admin).post(BASE + "contacts/", {"company": company.data["id"], "name": "Synthetic founder", "email": "founder@sync.example"}, format="json")
    assert contact.status_code == 201
    # NORMAL_APPLY cannot be sent externally, so the test verifies the safe recorded pipeline.
    created = api(admin).post(BASE + "outreach/", {"campaign": str(campaign.pk), "contact": contact.data["id"], "channel": "EMAIL", "subject": "Private draft subject", "body": "Private draft body"}, format="json")
    assert created.status_code == 201
    outreach_url = BASE + f"outreach/{created.data['id']}/transition/"
    for status in ("TARGET_IDENTIFIED", "CONTACT_VERIFIED", "DRAFTED", "REVIEW_REQUIRED"):
        response = api(admin).post(outreach_url, {"status": status}, format="json")
        assert response.status_code == 200, response.data
    customer_rows = api(owner).get(BASE + "outreach/", {"campaign": campaign.pk}).json()
    assert len(customer_rows) == 1
    row = customer_rows[0]
    assert row["status"] == "REVIEW_REQUIRED"
    assert row["company_name"] == "Outreach sync company"
    assert row["contact_name"] == "Synthetic founder"
    assert not {"body", "subject", "notes", "contact", "thread_reference"}.intersection(row)
    assert api(outsider).get(BASE + "outreach/", {"campaign": campaign.pk}).status_code == 404
    assert api(owner).post(outreach_url, {"status": "CLOSED"}, format="json").status_code == 403
