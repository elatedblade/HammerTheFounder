import uuid
from django.db import models


class Job(models.Model):
    class Status(models.TextChoices):
        OPEN = "OPEN", "Open"
        CLOSED = "CLOSED", "Closed"
        ARCHIVED = "ARCHIVED", "Archived"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey("companies.Company", on_delete=models.PROTECT, related_name="jobs")
    title = models.CharField(max_length=250)
    canonical_url = models.URLField(max_length=1000, blank=True)
    external_source = models.CharField(max_length=100, blank=True)
    external_id = models.CharField(max_length=250, blank=True)
    identity_key = models.CharField(max_length=64, unique=True, editable=False)
    location = models.CharField(max_length=200, blank=True)
    employment_type = models.CharField(max_length=100, blank=True)
    description = models.TextField(max_length=30000, blank=True)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.OPEN)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at", "id")
        constraints = [
            models.UniqueConstraint(fields=("canonical_url",), condition=~models.Q(canonical_url=""), name="job_canonical_url_unique"),
            models.UniqueConstraint(fields=("external_source", "external_id"), condition=~models.Q(external_source="") & ~models.Q(external_id=""), name="job_source_id_unique"),
        ]
