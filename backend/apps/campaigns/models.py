import uuid

from django.db import models

from apps.candidates.models import CandidateProfile


class Campaign(models.Model):
    class Plan(models.TextChoices):
        NORMAL_APPLY = "NORMAL_APPLY", "Normal Apply"
        COLD_APPLY = "COLD_APPLY", "Cold Apply"
        FULL_THROTTLE = "FULL_THROTTLE", "Full-Throttle Sprint"

    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        ONBOARDING = "ONBOARDING", "Onboarding"
        READY = "READY", "Ready"
        ACTIVE = "ACTIVE", "Active"
        PAUSED = "PAUSED", "Paused"
        COMPLETED = "COMPLETED", "Completed"
        CANCELLED = "CANCELLED", "Cancelled"

    class BillingStatus(models.TextChoices):
        PENDING = "PENDING", "Pending"
        ACTIVE = "ACTIVE", "Active"
        PAST_DUE = "PAST_DUE", "Past due"
        CANCELLED = "CANCELLED", "Cancelled"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    candidate = models.ForeignKey(
        CandidateProfile, on_delete=models.CASCADE, related_name="campaigns"
    )
    plan = models.CharField(max_length=20, choices=Plan.choices)
    status = models.CharField(
        max_length=16, choices=Status.choices, default=Status.DRAFT
    )
    start_date = models.DateField(null=True, blank=True)
    trial_end_date = models.DateField(null=True, blank=True)
    billing_status = models.CharField(
        max_length=16,
        choices=BillingStatus.choices,
        default=BillingStatus.PENDING,
    )
    settings_json = models.JSONField(default=dict)
    version = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at", "-id")
        indexes = [
            models.Index(fields=("candidate", "status")),
            models.Index(fields=("status", "created_at")),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(version__gte=1), name="campaign_version_positive"
            ),
        ]

    def __str__(self):
        return f"{self.get_plan_display()} for {self.candidate}"
