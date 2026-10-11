import uuid
from django.db import models
from django.utils.text import slugify


def normalize_company_name(value):
    """Return the stable comparison form used for duplicate company names."""
    return " ".join(str(value).split()).casefold()


class Company(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    normalized_name = models.CharField(max_length=200, unique=True, editable=False)
    identity_key = models.CharField(max_length=300, unique=True, editable=False)
    website = models.URLField(max_length=500, blank=True)
    industry = models.CharField(max_length=200, blank=True)
    location = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    metadata_json = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("name", "id")

    def save(self, *args, **kwargs):
        self.name = self.name.strip()
        self.normalized_name = normalize_company_name(self.name)
        if not self.identity_key:
            website_host = self.website.strip().casefold().removeprefix("www.")
            self.identity_key = f"domain:{website_host}" if website_host else f"name:{slugify(self.normalized_name)}"
        super().save(*args, **kwargs)
