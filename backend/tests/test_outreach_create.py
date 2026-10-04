from unittest.mock import patch
import pytest
from rest_framework.test import APIClient
from apps.users.models import User
from apps.candidates.models import CandidateProfile
from apps.campaigns.models import Campaign
from apps.companies.models import Company
from apps.contacts.models import Contact
from apps.outreach.models import Outreach, Suppression
from apps.tasks.models import HumanTask
from apps.events.models import Event

pytestmark = pytest.mark.django_db
URL = "/api/v1/outreach/create/"


@pytest.fixture
def setup():
    operator = User.objects.create_user("clerk", "outreach-op", email="op@example.com", role="OPERATOR")
    owner = User.objects.create_user("clerk", "outreach-owner", email="owner@example.com")
    candidate = CandidateProfile.objects.create(user=owner, full_name="Ada")
    campaign = Campaign.objects.create(candidate=candidate, plan="FULL_THROTTLE", status="ACTIVE", assigned_to=operator)
    client = APIClient()
    client.force_authenticate(operator)
    payload = {"campaign": str(campaign.pk), "company_data": {"name": "Acme", "website": "https://acme.example"}, "contact_data": {"name": "Founder", "email": "founder@acme.example"}, "channel": "EMAIL", "body": "Hello"}
    return client, payload, owner, campaign


def test_atomic_draft_and_review_task_reuses_dependencies(setup):
    client, payload, *_ = setup
    response = client.post(URL, payload, format="json")
    assert response.status_code == 201, response.data
    outreach = Outreach.objects.get()
    assert outreach.status == "DRAFT" and outreach.sent_at is None
    assert HumanTask.objects.filter(task_type="CONTACT_VERIFICATION").count() == 1
    assert Event.objects.filter(event_type="outreach.created").count() == 1
    assert client.post(URL, payload, format="json").status_code == 409
    assert Company.objects.count() == Contact.objects.count() == Outreach.objects.count() == 1
    existing = {"campaign": payload["campaign"], "contact": str(outreach.contact_id), "channel": "LINKEDIN", "body": "Hi"}
    assert client.post(URL, existing, format="json").status_code == 201


def test_suppression_rolls_back_dependencies_and_audit(setup):
    client, payload, *_ = setup
    Suppression.objects.create(email="founder@acme.example", reason="Opt out")
    assert client.post(URL, payload, format="json").status_code == 409
    assert not Company.objects.exists() and not Contact.objects.exists()
    assert not Outreach.objects.exists() and not Event.objects.exists()


def test_new_contact_with_existing_company_and_exclusive_relationships(setup):
    client, payload, *_ = setup
    company = Company.objects.create(name="Existing", identity_key="existing-company")
    payload.pop("company_data")
    payload["company"] = str(company.pk)
    assert client.post(URL, payload, format="json").status_code == 201
    assert Company.objects.count() == 1
    contact = Contact.objects.get()
    assert contact.company == company
    payload["contact"] = str(contact.pk)
    assert client.post(URL, payload, format="json").status_code == 400
    assert Outreach.objects.count() == 1


def test_task_failure_rolls_back_all_records(setup):
    client, payload, *_ = setup
    with patch("apps.operations.services.review_task", side_effect=RuntimeError("review failure")):
        with pytest.raises(RuntimeError):
            client.post(URL, payload, format="json")
    assert not Company.objects.exists() and not Contact.objects.exists()
    assert not Outreach.objects.exists() and not Event.objects.exists()


def test_scope_closed_campaign_and_client_permissions(setup):
    client, payload, owner, campaign = setup
    client.force_authenticate(owner)
    assert client.post(URL, payload, format="json").status_code == 403
    other = User.objects.create_user("clerk", "other-outreach", role="OPERATOR")
    client.force_authenticate(other)
    assert client.post(URL, payload, format="json").status_code == 404
    client.force_authenticate(campaign.assigned_to)
    campaign.status = "COMPLETED"
    campaign.save()
    assert client.post(URL, payload, format="json").status_code == 409
    assert not Company.objects.exists()


@pytest.mark.parametrize("change", [{"status": "SENT"}, {"contact_data": {"name": "A", "email": "invalid"}}, {"company_data": {}}, {"body": ""}])
def test_invalid_payload_creates_nothing(setup, change):
    client, payload, *_ = setup
    assert client.post(URL, {**payload, **change}, format="json").status_code == 400
    assert not Company.objects.exists() and not Contact.objects.exists()
