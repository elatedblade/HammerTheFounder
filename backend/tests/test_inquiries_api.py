import pytest
from django.urls import reverse
from django.test import override_settings
from rest_framework.test import APIClient

from apps.candidates.models import CandidateProfile
from apps.campaigns.models import Campaign
from apps.inquiries.models import Inquiry
from apps.inquiries.services import create_inquiry, convert_inquiry
from apps.users.models import User

pytestmark = pytest.mark.django_db


def make_user(subject, role=User.Role.CLIENT, active=True):
    return User.objects.create_user("clerk", subject, email=f"{subject}@example.com", role=role, is_active=active)


def api(user):
    client = APIClient(); client.force_authenticate(user=user); return client


@override_settings(WHATSAPP_BUSINESS_NUMBER="919876543210")
def test_create_is_owned_validated_and_retry_safe():
    client = make_user("client")
    response = api(client).post(reverse("inquiries:candidate-list"), {"plan": "NORMAL_APPLY"}, format="json")
    assert response.status_code == 201
    repeated = api(client).post(reverse("inquiries:candidate-list"), {"plan": "NORMAL_APPLY"}, format="json")
    assert repeated.status_code == 201 and repeated.data["id"] == response.data["id"]
    assert api(client).post(reverse("inquiries:candidate-list"), {"plan": "NORMAL_APPLY", "extra": 1}, format="json").status_code == 400
    assert "Normal%20Apply" in response.data["whatsapp_url"]


def test_missing_or_invalid_whatsapp_fails_before_write(settings):
    settings.WHATSAPP_BUSINESS_NUMBER = " +919876543210"
    client = make_user("client")
    response = api(client).post(reverse("inquiries:candidate-list"), {"plan": "COLD_APPLY"}, format="json")
    assert response.status_code == 503 and not Inquiry.objects.exists()


@override_settings(WHATSAPP_BUSINESS_NUMBER="919876543210")
def test_contacted_retry_and_customer_scope_are_bounded():
    client = make_user("client")
    inquiry = create_inquiry(user=client, plan=Inquiry.Plan.COLD_APPLY)
    inquiry.status = Inquiry.Status.CONTACTED; inquiry.save(update_fields=("status",))
    assert create_inquiry(user=client, plan=Inquiry.Plan.COLD_APPLY).id == inquiry.id
    other = make_user("other"); create_inquiry(user=other, plan=Inquiry.Plan.COLD_APPLY)
    assert len(api(client).get(reverse("inquiries:candidate-list")).data) == 1


@override_settings(WHATSAPP_BUSINESS_NUMBER="919876543210")
def test_admin_transition_audit_conversion_idempotency_and_closed_guard():
    admin = make_user("admin", User.Role.ADMIN)
    client = make_user("client")
    inquiry = create_inquiry(user=client, plan=Inquiry.Plan.FULL_THROTTLE)
    assert api(admin).patch(reverse("inquiries:admin-detail", args=[inquiry.id]), {"status": "CONTACTED"}, format="json").status_code == 200
    assert api(admin).patch(reverse("inquiries:admin-detail", args=[inquiry.id]), {"status": "OPEN"}, format="json").status_code == 409
    profile = CandidateProfile.objects.create(user=client, full_name="Client")
    converted = api(admin).post(reverse("inquiries:admin-convert", args=[inquiry.id]), {}, format="json")
    assert converted.status_code == 200 and converted.data["inquiry"]["status"] == "CONVERTED"
    again = api(admin).post(reverse("inquiries:admin-convert", args=[inquiry.id]), {}, format="json")
    assert again.data["campaign_id"] == converted.data["campaign_id"] and Campaign.objects.filter(candidate=profile).count() == 1
    assert api(admin).get(reverse("inquiries:admin-detail", args=[inquiry.id])).status_code == 200


def test_client_and_operator_permissions_and_not_found():
    client = make_user("client")
    assert api(client).get(reverse("inquiries:admin-list")).status_code == 403
    admin = make_user("admin", User.Role.ADMIN)
    import uuid
    assert api(admin).get(reverse("inquiries:admin-detail", args=[uuid.uuid4()])).status_code == 404


def test_inactive_client_cannot_create(settings):
    settings.WHATSAPP_BUSINESS_NUMBER = "919876543210"
    assert api(make_user("inactive", active=False)).post(reverse("inquiries:candidate-list"), {"plan": "NORMAL_APPLY"}, format="json").status_code == 403


@pytest.mark.parametrize("number", ["", "0", "01234567890", "91987", "9" * 16, "١٢٣٤٥٦٧٨٩", "919876543210/evil", "+919876543210"])
def test_public_contact_does_not_claim_invalid_destinations_are_ready(settings, number):
    settings.WHATSAPP_BUSINESS_NUMBER = number
    response = APIClient().get(reverse("inquiries:public-contact"))
    assert response.status_code == 200
    assert response.data == {"whatsapp_configured": False}


@override_settings(WHATSAPP_BUSINESS_NUMBER="15555550123")
def test_inquiry_creation_is_audited_once_and_does_not_create_a_profile_or_campaign():
    from apps.events.models import Event
    client = make_user("inquiry-only")
    first = create_inquiry(user=client, plan=Inquiry.Plan.NORMAL_APPLY)
    second = create_inquiry(user=client, plan=Inquiry.Plan.NORMAL_APPLY)
    assert first.id == second.id
    assert Event.objects.filter(event_type="inquiry.created", actor=client, client_visible=False).count() == 1
    assert not CandidateProfile.objects.exists()
    assert not Campaign.objects.exists()


@override_settings(WHATSAPP_BUSINESS_NUMBER="15555550123")
def test_admin_can_convert_but_not_activate_and_clients_cannot_mutate_ownership():
    owner = make_user("owner")
    outsider = make_user("outsider")
    operator = make_user("operator", User.Role.OPERATOR)
    admin = make_user("admin", User.Role.ADMIN)
    profile = CandidateProfile.objects.create(user=owner)
    inquiry = create_inquiry(user=owner, plan=Inquiry.Plan.COLD_APPLY)
    target = reverse("inquiries:admin-convert", args=[inquiry.pk])
    assert api(outsider).post(target, {}, format="json").status_code == 403
    assert api(operator).post(target, {}, format="json").status_code == 403
    assert api(admin).post(target, {"user_id": outsider.pk}, format="json").status_code == 400
    response = api(admin).post(target, {}, format="json")
    assert response.status_code == 200
    campaign = Campaign.objects.get(pk=response.data["campaign_id"])
    assert campaign.candidate_id == profile.pk
    assert campaign.plan == "COLD_APPLY" and campaign.status == "DRAFT"
    assert campaign.billing_status == "PENDING" and campaign.start_date is None


@override_settings(WHATSAPP_BUSINESS_NUMBER="15555550123")
def test_operator_can_work_preprofile_intake_but_not_another_operators_active_customer():
    owner = make_user("owner")
    other_owner = make_user("other-owner")
    operator = make_user("operator", User.Role.OPERATOR)
    other_operator = make_user("other-operator", User.Role.OPERATOR)
    intake = create_inquiry(user=owner, plan=Inquiry.Plan.NORMAL_APPLY)
    restricted = create_inquiry(user=other_owner, plan=Inquiry.Plan.NORMAL_APPLY)
    profile = CandidateProfile.objects.create(user=other_owner)
    Campaign.objects.create(candidate=profile, plan="NORMAL_APPLY", status="ACTIVE", assigned_to=other_operator)
    records = api(operator).get(reverse("inquiries:admin-list"))
    assert [str(row["id"]) for row in records.data] == [str(intake.pk)]
    assert api(operator).patch(reverse("inquiries:admin-detail", args=[intake.pk]), {"status": "CONTACTED"}, format="json").status_code == 200
    assert api(operator).get(reverse("inquiries:admin-detail", args=[restricted.pk])).status_code == 404
    assert api(operator).patch(reverse("inquiries:admin-detail", args=[restricted.pk]), {"status": "CONTACTED"}, format="json").status_code == 404


@override_settings(WHATSAPP_BUSINESS_NUMBER="15555550123")
def test_closed_inquiries_cannot_convert_and_customer_never_receives_internal_notes():
    owner = make_user("owner")
    admin = make_user("admin", User.Role.ADMIN)
    CandidateProfile.objects.create(user=owner)
    inquiry = create_inquiry(user=owner, plan=Inquiry.Plan.NORMAL_APPLY)
    api(admin).patch(reverse("inquiries:admin-detail", args=[inquiry.pk]), {"status": "CLOSED", "notes": "Private operator-only context"}, format="json")
    assert api(admin).post(reverse("inquiries:admin-convert", args=[inquiry.pk]), {}, format="json").status_code == 409
    data = api(owner).get(reverse("inquiries:candidate-list")).data[0]
    assert data["whatsapp_url"] is None and "notes" not in data
    assert "customer_email" not in data and not Campaign.objects.exists()


@override_settings(WHATSAPP_BUSINESS_NUMBER="15555550123")
def test_deactivated_identity_cannot_reuse_existing_inquiry_and_new_inquiries_are_rate_bounded():
    from rest_framework.exceptions import PermissionDenied
    from apps.inquiries.services import InquiryCreationThrottled
    owner = make_user("owner")
    inquiry = create_inquiry(user=owner, plan=Inquiry.Plan.NORMAL_APPLY)
    User.objects.filter(pk=owner.pk).update(is_active=False)
    with pytest.raises(PermissionDenied):
        create_inquiry(user=owner, plan=Inquiry.Plan.NORMAL_APPLY)
    User.objects.filter(pk=owner.pk).update(is_active=True)
    inquiry.status = "CLOSED"
    inquiry.save()
    for i in range(4):
        Inquiry.objects.create(user=owner, plan="NORMAL_APPLY", status="CLOSED", reference=f"RATE-FIXTURE-{i}")
    with pytest.raises(InquiryCreationThrottled):
        create_inquiry(user=owner, plan=Inquiry.Plan.COLD_APPLY)
