from django.conf import settings
from django.db import IntegrityError, transaction
from django.utils import timezone
from datetime import timedelta
import re
import uuid
from rest_framework.exceptions import APIException, ValidationError
from rest_framework.exceptions import PermissionDenied
from apps.candidates.models import CandidateProfile
from apps.campaigns.services import create_campaign
from apps.events.services import record_event
from apps.operations.common import administrator, require_operator
from apps.users.models import User
from .models import Inquiry
from .selectors import operational_inquiries


class WhatsAppNotConfigured(APIException):
    status_code = 503
    default_code = "whatsapp_not_configured"
    default_detail = "WhatsApp contact is not configured yet."


class MissingInquiryProfile(APIException):
    status_code = 409
    default_code = "inquiry_profile_required"
    default_detail = "Complete the customer profile before converting this inquiry to a campaign."


class InquiryCreationThrottled(APIException):
    status_code = 429
    default_code = "inquiry_rate_limited"
    default_detail = "Too many new inquiries. Please try again shortly."


class InvalidInquiryTransition(APIException):
    status_code = 409
    default_code = "invalid_inquiry_transition"
    default_detail = "That inquiry transition is not allowed."


def whatsapp_configured():
    value = getattr(settings, "WHATSAPP_BUSINESS_NUMBER", "")
    return valid_whatsapp_number(value)


def valid_whatsapp_number(value):
    return bool(isinstance(value, str) and re.fullmatch(r"[1-9][0-9]{7,14}", value, flags=re.ASCII))


def create_inquiry(*, user, plan):
    if not user or not user.is_authenticated or not user.is_active or user.role != "CLIENT":
        raise PermissionDenied("An active client identity is required.")
    if plan not in Inquiry.Plan.values:
        raise ValidationError({"plan": "Choose a valid service plan."})
    if not whatsapp_configured():
        raise WhatsAppNotConfigured()
    try:
        with transaction.atomic():
            locked = User.objects.select_for_update().get(pk=user.pk)
            if locked.role != locked.Role.CLIENT or not locked.is_active:
                raise PermissionDenied("An active client identity is required.")
            existing = Inquiry.objects.filter(user=locked, plan=plan, status__in=(Inquiry.Status.OPEN, Inquiry.Status.CONTACTED)).first()
            if existing:
                return existing
            recent = Inquiry.objects.filter(user=locked, created_at__gte=timezone.now() - timedelta(minutes=1)).count()
            if recent >= 5:
                raise InquiryCreationThrottled()
            inquiry = Inquiry.objects.create(user=locked, plan=plan, reference=f"HTF-{uuid.uuid4().hex.upper()}")
            record_event(
                actor=locked,
                event_type="inquiry.created",
                summary="Customer selected a service plan for discussion.",
                payload={"inquiry_id": str(inquiry.pk), "plan": plan},
                client_visible=False,
            )
            return inquiry
    except IntegrityError:
        existing = Inquiry.objects.filter(user=user, plan=plan, status__in=(Inquiry.Status.OPEN, Inquiry.Status.CONTACTED)).first()
        if existing:
            return existing
        raise InvalidInquiryTransition("The inquiry could not be saved. Please retry.")


@transaction.atomic
def update_inquiry(*, inquiry_id, actor, data):
    require_operator(actor)
    from django.shortcuts import get_object_or_404
    inquiry = get_object_or_404(operational_inquiries(actor).select_for_update(of=("self",)), pk=inquiry_id)
    target = data.get("status")
    allowed = {Inquiry.Status.OPEN: {Inquiry.Status.CONTACTED, Inquiry.Status.CLOSED}, Inquiry.Status.CONTACTED: {Inquiry.Status.CLOSED}}
    if target and target != inquiry.status and target not in allowed.get(inquiry.status, set()):
        raise InvalidInquiryTransition()
    before = inquiry.status
    if target: inquiry.status = target
    if "notes" in data: inquiry.notes = data["notes"]
    inquiry.save()
    record_event(event_type="inquiry.updated", actor=actor, summary="Inquiry updated.", payload={"inquiry_id": str(inquiry.id), "before": before, "after": inquiry.status}, client_visible=False)
    return inquiry


@transaction.atomic
def convert_inquiry(*, inquiry_id, actor):
    from apps.operations.common import require_admin
    require_admin(actor)
    from django.shortcuts import get_object_or_404
    inquiry = get_object_or_404(operational_inquiries(actor).select_for_update(of=("self",)), pk=inquiry_id)
    if inquiry.campaign_id:
        return inquiry, inquiry.campaign
    if inquiry.status not in {Inquiry.Status.OPEN, Inquiry.Status.CONTACTED}:
        raise InvalidInquiryTransition()
    candidate = CandidateProfile.objects.filter(user=inquiry.user, user__role="CLIENT", user__is_active=True).first()
    if candidate is None:
        raise MissingInquiryProfile()
    campaign = create_campaign(candidate_id=candidate.id, plan=inquiry.plan, actor=actor)
    inquiry.campaign = campaign
    inquiry.status = Inquiry.Status.CONVERTED
    inquiry.save(update_fields=("campaign", "status", "updated_at"))
    record_event(campaign=campaign, actor=actor, event_type="inquiry.converted", summary="Inquiry converted to campaign.", payload={"inquiry_id": str(inquiry.id), "reference": inquiry.reference}, client_visible=False)
    return inquiry, campaign
