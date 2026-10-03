import uuid
from django.db import models


class Suppression(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    reason = models.CharField(max_length=1000)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at", "id")


class OutreachTemplate(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200, unique=True)
    subject = models.CharField(max_length=500, blank=True)
    body = models.TextField(max_length=20000)

    class Meta:
        ordering = ("name", "id")


class Outreach(models.Model):
    class Channel(models.TextChoices):
        EMAIL = "EMAIL", "Email"
        LINKEDIN = "LINKEDIN", "LinkedIn"
        WHATSAPP = "WHATSAPP", "WhatsApp"

    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        READY = "READY", "Ready"
        TARGET_IDENTIFIED = "TARGET_IDENTIFIED", "Target identified"
        CONTACT_VERIFIED = "CONTACT_VERIFIED", "Contact verified"
        DRAFTED = "DRAFTED", "Drafted"
        REVIEW_REQUIRED = "REVIEW_REQUIRED", "Review required"
        SENT = "SENT", "Sent"
        DELIVERED = "DELIVERED", "Delivered"
        REPLIED = "REPLIED", "Replied"
        POSITIVE_REPLY = "POSITIVE_REPLY", "Positive reply"
        NEGATIVE_REPLY = "NEGATIVE_REPLY", "Negative reply"
        BOUNCED = "BOUNCED", "Bounced"
        CLOSED = "CLOSED", "Closed"
        SUPPRESSED = "SUPPRESSED", "Suppressed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    campaign = models.ForeignKey("campaigns.Campaign", on_delete=models.CASCADE, related_name="outreach")
    contact = models.ForeignKey("contacts.Contact", on_delete=models.PROTECT, related_name="outreach")
    channel = models.CharField(max_length=16, choices=Channel.choices, default=Channel.EMAIL)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    subject = models.CharField(max_length=500, blank=True)
    body = models.TextField(max_length=20000, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    bounced_at = models.DateTimeField(null=True, blank=True)
    reply_at = models.DateTimeField(null=True, blank=True)
    follow_up_due_at = models.DateTimeField(null=True, blank=True)
    thread_reference = models.CharField(max_length=1000, blank=True)
    notes = models.TextField(max_length=10000, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at", "id")
        constraints = [models.UniqueConstraint(fields=("campaign", "contact", "channel"), name="outreach_campaign_contact_channel_unique")]
        indexes = [models.Index(fields=("campaign", "status"))]
