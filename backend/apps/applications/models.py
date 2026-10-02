import uuid

from django.core.exceptions import ValidationError
from django.db import models

from apps.campaigns.models import Campaign
from apps.candidates.models import CandidateProfile
from apps.jobs.models import Job
from apps.users.models import User


class Application(models.Model):
    class Status(models.TextChoices):
        DISCOVERED = "DISCOVERED", "Discovered"
        SHORTLISTED = "SHORTLISTED", "Shortlisted"
        QUEUED = "QUEUED", "Queued"
        IN_PROGRESS = "IN_PROGRESS", "In progress"
        SUBMITTED = "SUBMITTED", "Submitted"
        APPLICATION_FAILED = "APPLICATION_FAILED", "Application failed"
        IN_REVIEW = "IN_REVIEW", "In review"
        RECRUITER_CONTACTED = "RECRUITER_CONTACTED", "Recruiter contacted"
        INTERVIEW = "INTERVIEW", "Interview"
        INTERVIEW_SCHEDULED = "INTERVIEW_SCHEDULED", "Interview scheduled"
        OFFER = "OFFER", "Offer"
        REJECTED = "REJECTED", "Rejected"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    campaign = models.ForeignKey(
        Campaign, on_delete=models.CASCADE, related_name="applications"
    )
    job = models.ForeignKey(Job, on_delete=models.PROTECT, related_name="applications")
    # Candidate is denormalized from campaign so the database can enforce the
    # business key (candidate, job). The service/model save path keeps it in sync.
    candidate = models.ForeignKey(
        CandidateProfile,
        on_delete=models.CASCADE,
        related_name="applications",
        editable=False,
    )
    status = models.CharField(
        max_length=24,
        choices=Status.choices,
        default=Status.DISCOVERED,
    )
    submitted_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    operator = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="managed_applications",
    )
    source_reference = models.CharField(max_length=2048, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at", "-id")
        constraints = [
            models.UniqueConstraint(
                fields=("candidate", "job"),
                name="applications_candidate_job_unique",
            ),
        ]
        indexes = [
            models.Index(fields=("campaign", "status")),
            models.Index(fields=("status", "created_at")),
        ]

    def save(self, *args, **kwargs):
        if self.campaign_id:
            campaign_candidate_id = self.campaign.candidate_id
            if self.candidate_id and self.candidate_id != campaign_candidate_id:
                raise ValidationError("Application candidate must match its campaign.")
            self.candidate_id = campaign_candidate_id
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.job} for {self.candidate} ({self.status})"
