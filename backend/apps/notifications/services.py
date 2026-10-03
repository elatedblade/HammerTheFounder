from datetime import timedelta
import re
from django.db import transaction
from django.utils import timezone
from django.core.validators import validate_email
from rest_framework.exceptions import ValidationError
from apps.billing.services import Conflict, require_operator, get_visible_campaign
from apps.events.services import record_event
from apps.integrations.email.resend import configuration, deliver, EmailDeliveryError, EmailNotConfigured
from .models import Notification


def validate_whatsapp_recipient(campaign, recipient):
    def normalize(value):
        value = re.sub(r"[\s().-]", "", value or "")
        return value.lstrip("+") if re.fullmatch(r"\+?[0-9]{7,15}", value) else None
    phone = normalize(campaign.candidate.user.phone)
    if phone is None:
        raise ValidationError({"recipient": "The campaign customer's valid phone must be saved before recording a WhatsApp communication."})
    if normalize(recipient) != phone:
        raise ValidationError({"recipient": "WhatsApp recipient must match the campaign customer's saved phone, including country code."})


def create_notification(*, user, data):
    require_operator(user)
    campaign = get_visible_campaign(user, data["campaign"])
    # Transactional delivery is limited to the campaign customer, never cold leads.
    if data["channel"] == "EMAIL":
        try:
            validate_email(data["recipient"])
        except Exception as exc:
            raise ValidationError({"recipient": "A valid email is required."}) from exc
        if data["recipient"].casefold() != campaign.candidate.user.email.casefold():
            raise ValidationError({"recipient": "Only the campaign customer's email is permitted."})
    else:
        validate_whatsapp_recipient(campaign, data["recipient"])
    with transaction.atomic():
        notification = Notification.objects.create(created_by=user, **{**data, "campaign": campaign})
        record_event(campaign=campaign, actor=user, event_type="NOTIFICATION_CREATED", summary="Customer communication drafted.", payload={"notification_id": str(notification.pk)}, client_visible=False)
        return notification


def dispatch_notification(*, user, notification_id, manual=False):
    require_operator(user)
    notification = Notification.objects.get(pk=notification_id)
    get_visible_campaign(user, notification.campaign_id)
    if not manual:
        configuration()
    with transaction.atomic():
        notification = Notification.objects.select_for_update().get(pk=notification_id)
        if notification.status == "SENT":
            return notification
        if manual:
            if notification.channel != "WHATSAPP" or notification.status != "DRAFT":
                raise Conflict("Only draft WhatsApp communications can be manually marked sent.")
            validate_whatsapp_recipient(notification.campaign, notification.recipient)
            notification.status = "SENT"
            notification.sent_at = timezone.now()
            notification.save()
            record_event(campaign=notification.campaign, actor=user, event_type="NOTIFICATION_SENT", summary="WhatsApp communication manually marked sent.", payload={"notification_id": str(notification.pk)})
        else:
            if notification.channel != "EMAIL":
                raise Conflict("WhatsApp delivery is manual only.")
            if notification.status in {"QUEUED", "SENDING"}:
                return notification
            if notification.status != "DRAFT":
                raise Conflict("Failed or uncertain delivery requires operator reconciliation; create a new draft only after checking provider state.")
            notification.status = "QUEUED"
            notification.queued_at = timezone.now()
            notification.save(update_fields=["status", "queued_at"])
            transaction.on_commit(lambda: enqueue_notification(str(notification.pk)))
    return notification


def enqueue_notification(pk):
    from .tasks import send_notification
    try:
        send_notification.delay(pk)
    except Exception:
        Notification.objects.filter(pk=pk, status="QUEUED").update(status="FAILED", error_code="queue_unavailable")


def deliver_notification(pk):
    with transaction.atomic():
        item = Notification.objects.select_for_update().get(pk=pk)
        if item.status == "SENDING" and item.started_at and item.started_at < timezone.now() - timedelta(minutes=5):
            item.status = "UNKNOWN"
            item.error_code = "delivery_interrupted"
            item.save()
            return
        if item.status != "QUEUED":
            return
        if item.channel != "EMAIL" or item.recipient.casefold() != item.campaign.candidate.user.email.casefold():
            item.status = "FAILED"
            item.error_code = "recipient_not_current_customer"
            item.save()
            return
        if item.started_at and item.started_at < timezone.now() - timedelta(hours=23):
            item.status = "UNKNOWN"
            item.error_code = "idempotency_window_expired"
            item.save()
            return
        item.status = "SENDING"
        item.started_at = item.started_at or timezone.now()
        item.attempts += 1
        item.save()
    try:
        provider_id = deliver(recipient=item.recipient, subject=item.subject, body=item.body, idempotency_key="notification/" + str(item.pk))
    except EmailDeliveryError as exc:
        retry = exc.retryable and item.attempts < 3
        uncertain = exc.retryable or exc.code == "invalid_provider_response"
        Notification.objects.filter(pk=pk, status="SENDING").update(status="QUEUED" if retry else "UNKNOWN" if uncertain else "FAILED", error_code=exc.code)
        if retry:
            raise
        return
    except EmailNotConfigured:
        Notification.objects.filter(pk=pk, status="SENDING").update(status="FAILED", error_code="delivery_configuration_error")
        return
    except Exception:
        Notification.objects.filter(pk=pk, status="SENDING").update(status="UNKNOWN", error_code="delivery_interrupted")
        return
    with transaction.atomic():
        item = Notification.objects.select_for_update().get(pk=pk)
        if item.status != "SENDING":
            return
        item.status = "SENT"
        item.provider_id = provider_id
        item.sent_at = timezone.now()
        item.error_code = ""
        item.save()
        record_event(campaign=item.campaign, actor=item.created_by, event_type="NOTIFICATION_SENT", summary="Transactional email delivered to provider.", payload={"notification_id": str(item.pk)})
