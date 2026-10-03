import uuid
from django.conf import settings
from django.db import models


class Notification(models.Model):
    class Channel(models.TextChoices):
        EMAIL = "EMAIL"
        WHATSAPP = "WHATSAPP"

    class Status(models.TextChoices):
        DRAFT = "DRAFT"
        QUEUED = "QUEUED"
        SENDING = "SENDING"
        SENT = "SENT"
        FAILED = "FAILED"
        UNKNOWN = "UNKNOWN"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    campaign = models.ForeignKey("campaigns.Campaign", on_delete=models.PROTECT, related_name="notifications")
    channel = models.CharField(max_length=16, choices=Channel.choices)
    recipient = models.CharField(max_length=320)
    subject = models.CharField(max_length=255, blank=True)
    body = models.TextField()
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.DRAFT)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True)
    queued_at = models.DateTimeField(null=True)
    started_at = models.DateTimeField(null=True)
    attempts = models.PositiveSmallIntegerField(default=0)
    provider_id = models.CharField(max_length=128, blank=True)
    error_code = models.CharField(max_length=80, blank=True)

    class Meta:
        ordering = ("-created_at",)


class NotificationTemplate(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=128, unique=True)
    channel = models.CharField(max_length=16, choices=Notification.Channel.choices)
    subject = models.CharField(max_length=255, blank=True)
    body = models.TextField()
