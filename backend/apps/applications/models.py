import uuid
from django.db import models


class Application(models.Model):
    class Status(models.TextChoices):
        SAVED = "SAVED", "Saved"
        READY = "READY", "Ready"
        DISCOVERED = "DISCOVERED", "Discovered"
        SHORTLISTED = "SHORTLISTED", "Shortlisted"
        QUEUED = "QUEUED", "Queued"
        IN_PROGRESS = "IN_PROGRESS", "In progress"
        APPLICATION_FAILED = "APPLICATION_FAILED", "Application failed"
        SUBMITTED = "SUBMITTED", "Submitted"
        IN_REVIEW = "IN_REVIEW", "In review"
        RECRUITER_CONTACTED = "RECRUITER_CONTACTED", "Recruiter contacted"
        INTERVIEW = "INTERVIEW", "Interview"
        INTERVIEW_SCHEDULED = "INTERVIEW_SCHEDULED", "Interview scheduled"
        OFFER = "OFFER", "Offer"
        REJECTED = "REJECTED", "Rejected"
        WITHDRAWN = "WITHDRAWN", "Withdrawn"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    campaign = models.ForeignKey("campaigns.Campaign", on_delete=models.CASCADE, related_name="applications")
    candidate = models.ForeignKey("candidates.CandidateProfile", on_delete=models.CASCADE, related_name="applications", editable=False)
    job = models.ForeignKey("jobs.Job", on_delete=models.PROTECT, related_name="applications")
    status = models.CharField(max_length=24, choices=Status.choices, default=Status.SAVED)
    submitted_at = models.DateTimeField(null=True, blank=True)
    in_progress_at = models.DateTimeField(null=True, blank=True)
    failed_at = models.DateTimeField(null=True, blank=True)
    failure_reason = models.TextField(max_length=10000, blank=True)
    interview_scheduled_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(max_length=10000, blank=True)
    source_reference = models.CharField(max_length=1000, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at", "id")
        constraints = [
            models.CheckConstraint(condition=~models.Q(status="INTERVIEW_SCHEDULED") | models.Q(interview_scheduled_at__isnull=False), name="application_interview_date_required"),
            models.UniqueConstraint(fields=("campaign", "job"), name="application_campaign_job_unique"),
            models.UniqueConstraint(fields=("candidate", "job"), name="application_candidate_job_unique"),
        ]
        indexes = [models.Index(fields=("campaign", "status"))]

    def save(self, *args, **kwargs):
        self.candidate_id = self.campaign.candidate_id
        return super().save(*args, **kwargs)
