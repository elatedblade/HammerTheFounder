import uuid
from django.db import models
from django.utils import timezone
import hashlib


class Job(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
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
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.ACTIVE)
    fingerprint = models.CharField(max_length=64, blank=True)
    first_seen_at = models.DateTimeField(default=timezone.now, editable=False)
    last_seen_at = models.DateTimeField(default=timezone.now)
    metadata_json = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at", "id")
        constraints = [
            models.UniqueConstraint(fields=("canonical_url",), condition=~models.Q(canonical_url=""), name="job_canonical_url_unique"),
            models.UniqueConstraint(fields=("external_source", "external_id"), condition=~models.Q(external_source="") & ~models.Q(external_id=""), name="job_source_id_unique"),
        ]

    def save(self, *args, **kwargs):
        self.external_source = self.external_source.strip().casefold()
        self.external_id = self.external_id.strip()
        self.canonical_url = self.canonical_url.strip()
        if not self.identity_key:
            identity_value = self.canonical_url or "|".join(
                (str(self.company_id), self.external_source, self.external_id, self.title.strip(), self.location.strip())
            )
            self.identity_key = hashlib.sha256(identity_value.casefold().encode()).hexdigest()
        self.last_seen_at = timezone.now()
        super().save(*args, **kwargs)
