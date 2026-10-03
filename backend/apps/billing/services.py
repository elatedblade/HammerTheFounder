from django.db import IntegrityError, transaction
from django.utils import timezone
from rest_framework.exceptions import APIException, PermissionDenied
from rest_framework import serializers

from apps.campaigns.models import Campaign
from apps.campaigns.selectors import get_visible_campaign as select_visible_campaign
from django.http import Http404
from apps.events.services import record_event
from apps.users.models import User
from .models import Payment


class Conflict(APIException):
    status_code = 409
    default_code = "invalid_transition"
    default_detail = "This operation conflicts with the current state."


def get_visible_campaign(user, campaign_id):
    campaign = select_visible_campaign(user, campaign_id)
    if campaign is None:
        raise Http404
    return campaign


def filter_campaign(queryset, request):
    value = request.query_params.get("campaign")
    return queryset.filter(campaign_id=serializers.UUIDField().run_validation(value)) if value else queryset


def require_operator(user, *, admin=False):
    roles = {User.Role.ADMIN, User.Role.SUPERADMIN}
    if not admin:
        roles.add(User.Role.OPERATOR)
    if not user.is_authenticated or not user.is_active or user.role not in roles:
        raise PermissionDenied()


def create_payment(*, user, data, key=None):
    require_operator(user)
    campaign = get_visible_campaign(user, data["campaign"])
    values = {k: data[k] for k in ("amount", "currency", "notes") if k in data}
    try:
        with transaction.atomic():
            payment, created = Payment.objects.get_or_create(idempotency_key=key, defaults={"campaign": campaign, **values}) if key else (Payment.objects.create(campaign=campaign, **values), True)
            if not created and (payment.campaign_id != campaign.pk or payment.amount != data["amount"] or payment.currency != data.get("currency", "INR")):
                raise Conflict("Idempotency key was already used for a different payment.")
            if created:
                record_event(campaign=campaign, event_type="PAYMENT_CREATED", actor=user, summary="Payment recorded pending verification.", payload={"payment_id": str(payment.pk)})
            return payment, created
    except IntegrityError as exc:
        raise Conflict("Payment reference or idempotency key already exists.") from exc


def transition_payment(*, user, payment_id, target, reference="", notes=""):
    require_operator(user, admin=True)
    reference = reference.strip()
    if target == Payment.Status.VERIFIED and (not reference or len(reference) > 128):
        raise Conflict("A non-empty payment reference of at most 128 characters is required.")
    try:
        with transaction.atomic():
            payment = Payment.objects.select_for_update().get(pk=payment_id)
            campaign = Campaign.objects.select_for_update().get(pk=payment.campaign_id)
            if payment.status == target:
                if target == Payment.Status.VERIFIED and payment.reference != reference:
                    raise Conflict("Payment already verified with another reference.")
                return payment
            allowed = {Payment.Status.PENDING: {Payment.Status.VERIFIED, Payment.Status.FAILED}, Payment.Status.VERIFIED: {Payment.Status.REFUNDED}}
            if target not in allowed.get(payment.status, set()):
                raise Conflict()
            payment.status = target
            payment.notes = notes
            if target == Payment.Status.VERIFIED:
                payment.reference = reference
                payment.verified_by = user
                payment.verified_at = timezone.now()
            payment.save()
            campaign.billing_status = Campaign.BillingStatus.ACTIVE if Payment.objects.filter(campaign=campaign, status=Payment.Status.VERIFIED).exists() else Campaign.BillingStatus.PENDING
            campaign.version += 1
            campaign.save(update_fields=["billing_status", "version", "updated_at"])
            record_event(campaign=campaign, actor=user, event_type="PAYMENT_" + target, summary="Payment " + target.lower() + ".", payload={"payment_id": str(payment.pk), "reference": payment.reference, "notes": notes})
            return payment
    except IntegrityError as exc:
        raise Conflict("This payment reference has already been recorded.") from exc
