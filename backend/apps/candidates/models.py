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
    target_industries = models.JSONField(default=list, validators=[validate_profile_list])
    expected_ctc_min = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    expected_ctc_max = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    work_authorization = models.CharField(max_length=200, blank=True)
    sponsorship_requirement = models.CharField(max_length=200, blank=True)
    notice_period = models.CharField(max_length=200, blank=True)
    preferences_json = models.JSONField(default=dict)
    review_status = models.CharField(max_length=24, choices=[("PENDING", "Pending"), ("APPROVED", "Approved"), ("CHANGES_REQUESTED", "Changes requested")], default="PENDING")
    review_notes = models.TextField(max_length=10000, blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="reviewed_candidates")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)
        constraints = [
            models.CheckConstraint(condition=models.Q(expected_ctc_min__isnull=True) | models.Q(expected_ctc_min__gte=0), name="candidate_ctc_min_nonnegative"),
            models.CheckConstraint(condition=models.Q(expected_ctc_max__isnull=True) | models.Q(expected_ctc_max__gte=0), name="candidate_ctc_max_nonnegative"),
            models.CheckConstraint(condition=models.Q(expected_ctc_min__isnull=True) | models.Q(expected_ctc_max__isnull=True) | models.Q(expected_ctc_max__gte=models.F("expected_ctc_min")), name="candidate_ctc_ordered"),
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
