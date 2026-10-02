from django.core.exceptions import ValidationError
from django.db import models

from apps.users.models import User


def validate_profile_list(value):
    """Validate the persisted shape of a candidate's short string lists."""
    if not isinstance(value, list):
        raise ValidationError("This value must be a list.")
    if len(value) > 10:
        raise ValidationError("A maximum of 10 values is allowed.")
    if any(not isinstance(item, str) for item in value):
        raise ValidationError("Every value must be a string.")
    if any(not item or item != item.strip() or len(item) > 100 for item in value):
        raise ValidationError(
            "Values must be non-empty, trimmed strings of at most 100 characters."
        )
    if len(set(value)) != len(value):
        raise ValidationError("Values must be distinct.")


class CandidateProfile(models.Model):
    class RemotePreference(models.TextChoices):
        UNSPECIFIED = "UNSPECIFIED", "Unspecified"
        ONSITE = "ONSITE", "Onsite"
        HYBRID = "HYBRID", "Hybrid"
        REMOTE = "REMOTE", "Remote"
        FLEXIBLE = "FLEXIBLE", "Flexible"

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="candidate_profile",
    )
    full_name = models.CharField(max_length=150, blank=True)
    headline = models.CharField(max_length=200, blank=True)
    location = models.CharField(max_length=200, blank=True)
    experience_summary = models.TextField(max_length=5000, blank=True)
    target_roles = models.JSONField(
        default=list,
        validators=[validate_profile_list],
    )
    preferred_locations = models.JSONField(
        default=list,
        validators=[validate_profile_list],
    )
    remote_preference = models.CharField(
        max_length=12,
        choices=RemotePreference.choices,
        default=RemotePreference.UNSPECIFIED,
    )
    profile_version = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)
        constraints = [
            models.CheckConstraint(
                condition=models.Q(profile_version__gte=1),
                name="candidate_profile_version_positive",
            ),
        ]

    @property
    def basics_complete(self):
        return bool(
            self.full_name.strip()
            and self.location.strip()
            and self.experience_summary.strip()
            and self.target_roles
        )

    def __str__(self):
        return self.full_name or f"Candidate profile {self.pk}"
