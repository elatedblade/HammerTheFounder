import uuid

from django.db import models


def normalize_company_name(value):
    return " ".join(value.casefold().split())


class Company(models.Model):
    """Canonical organization record shared by operational workflows."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    normalized_name = models.CharField(max_length=255, unique=True, editable=False)
    website = models.URLField(max_length=2048, blank=True)
    industry = models.CharField(max_length=120, blank=True)
    location = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    metadata_json = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("name", "id")
        indexes = [
            models.Index(fields=("name",)),
        ]

    def save(self, *args, **kwargs):
        self.name = self.name.strip()
        self.normalized_name = normalize_company_name(self.name)
        super().save(*args, **kwargs)

    @property
    def metadata(self):
        """Short alias for callers that use the public API field name."""
        return self.metadata_json

    def __str__(self):
        return self.name
