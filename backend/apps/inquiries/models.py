import uuid
from django.conf import settings
from django.db import models


class Inquiry(models.Model):
    class Plan(models.TextChoices):
        NORMAL_APPLY = "NORMAL_APPLY", "Normal Apply"
        COLD_APPLY = "COLD_APPLY", "Cold Apply"
        FULL_THROTTLE = "FULL_THROTTLE", "Full-Throttle Sprint"

    class Status(models.TextChoices):
        OPEN = "OPEN", "Open"
        CONTACTED = "CONTACTED", "Contacted"
        CONVERTED = "CONVERTED", "Converted"
        CLOSED = "CLOSED", "Closed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="inquiries")
    plan = models.CharField(max_length=20, choices=Plan.choices)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.OPEN)
    reference = models.CharField(max_length=40, unique=True, editable=False)
    campaign = models.ForeignKey("campaigns.Campaign", null=True, blank=True, on_delete=models.SET_NULL, related_name="source_inquiries")
    notes = models.TextField(max_length=10000, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at", "-id")
        constraints = [models.UniqueConstraint(fields=("user", "plan"), condition=models.Q(status__in=("OPEN", "CONTACTED")), name="inquiry_one_open_plan_per_user")]
        indexes = [models.Index(fields=("status", "created_at"), name="inquiries_i_status_8d3c50_idx"), models.Index(fields=("user", "created_at"), name="inquiries_i_user_id_6a5c03_idx")]
