import uuid
from django.conf import settings
from django.db import models


class HumanTask(models.Model):
    class Status(models.TextChoices):
        OPEN = "OPEN", "Open"
        CLAIMED = "CLAIMED", "Claimed"
        COMPLETED = "COMPLETED", "Completed"
        CANCELLED = "CANCELLED", "Cancelled"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    campaign = models.ForeignKey("campaigns.Campaign", on_delete=models.CASCADE, related_name="human_tasks")
    task_type = models.CharField(max_length=100)
    priority = models.PositiveSmallIntegerField(default=3)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.OPEN)
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="human_tasks")
    payload_json = models.JSONField(default=dict)
    completion_notes = models.TextField(max_length=10000, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ("priority", "created_at", "id")
        constraints = [models.CheckConstraint(condition=models.Q(priority__gte=1, priority__lte=5), name="task_priority_range")]
        indexes = [models.Index(fields=("campaign", "status"))]
