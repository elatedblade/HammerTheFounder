import uuid
from django.conf import settings
from django.db import models


class AIRun(models.Model):
    class Capability(models.TextChoices):
        PROFILE_EXTRACT = "profile_extract"
        JOB_MATCH = "job_match"
        OUTREACH_DRAFT = "outreach_draft"
        QA = "qa"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    campaign = models.ForeignKey("campaigns.Campaign", on_delete=models.PROTECT, related_name="ai_runs")
    capability = models.CharField(max_length=32, choices=Capability.choices)
    status = models.CharField(max_length=16, default="QUEUED", choices=[(s, s) for s in ("QUEUED", "RUNNING", "SUCCEEDED", "FAILED")])
    input_json = models.JSONField(default=dict)
    result = models.JSONField(null=True)
    error_code = models.CharField(max_length=80, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    model_name = models.CharField(max_length=128, blank=True)
    agent_version = models.CharField(max_length=80, default="htf-assistance-v2")
    prompt_version = models.CharField(max_length=80, default="canonical-facts-v1")
    source_references = models.JSONField(default=dict)
    provider_request_id = models.CharField(max_length=128, blank=True)
    usage_json = models.JSONField(default=dict)
    duration_ms = models.PositiveIntegerField(null=True)
    attempts = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True)
    completed_at = models.DateTimeField(null=True)

    class Meta:
        ordering = ("-created_at",)
