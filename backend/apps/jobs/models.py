import uuid

from django.db import models

from apps.companies.models import Company


class Job(models.Model):
    """Normalized job opportunity record, deduplicated per external source."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(
        Company,
        on_delete=models.PROTECT,
        related_name="jobs",
    )
    external_source = models.CharField(max_length=100)
    external_id = models.CharField(max_length=255)
    canonical_url = models.URLField(max_length=2048, blank=True)
    title = models.CharField(max_length=300)
    location = models.CharField(max_length=255, blank=True)
    employment_type = models.CharField(max_length=64, blank=True)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=32, default="ACTIVE")
    fingerprint = models.CharField(max_length=128, blank=True)
    first_seen_at = models.DateTimeField(auto_now_add=True)
    last_seen_at = models.DateTimeField(auto_now=True)
    metadata_json = models.JSONField(default=dict)

    class Meta:
        ordering = ("-last_seen_at", "-id")
        constraints = [
            models.UniqueConstraint(
                fields=("external_source", "external_id"),
                name="jobs_external_source_id_unique",
            ),
        ]
        indexes = [
            models.Index(fields=("company", "status")),
            models.Index(fields=("external_source", "external_id")),
            models.Index(fields=("fingerprint",)),
        ]

    def save(self, *args, **kwargs):
        self.external_source = self.external_source.strip().casefold()
        self.external_id = self.external_id.strip()
        self.title = self.title.strip()
        self.location = self.location.strip()
        self.employment_type = self.employment_type.strip()
        self.fingerprint = self.fingerprint.strip()
        super().save(*args, **kwargs)

    @property
    def metadata(self):
        """Short alias for callers that use the public API field name."""
        return self.metadata_json

    def __str__(self):
        return f"{self.title} at {self.company}"
