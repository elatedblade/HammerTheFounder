import uuid

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from apps.candidates.models import CandidateProfile

from .constants import MAX_RESUME_FILE_SIZE


class Resume(models.Model):
    class UploadStatus(models.TextChoices):
        PENDING_UPLOAD = "PENDING_UPLOAD", "Pending upload"
        UPLOADED = "UPLOADED", "Uploaded"
        FAILED = "FAILED", "Failed"

    class ParseStatus(models.TextChoices):
        NOT_STARTED = "NOT_STARTED", "Not started"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    candidate = models.ForeignKey(
        CandidateProfile, on_delete=models.CASCADE, related_name="resumes"
    )
    s3_key = models.CharField(max_length=512, unique=True)
    original_filename = models.CharField(max_length=255)
    content_type = models.CharField(max_length=100)
    file_size = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(MAX_RESUME_FILE_SIZE)]
    )
    upload_status = models.CharField(
        max_length=16,
        choices=UploadStatus.choices,
        default=UploadStatus.PENDING_UPLOAD,
    )
    parse_status = models.CharField(
        max_length=16,
        choices=ParseStatus.choices,
        default=ParseStatus.NOT_STARTED,
    )
    version = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at", "-id")
        constraints = [
            models.CheckConstraint(
                condition=models.Q(file_size__gte=1, file_size__lte=MAX_RESUME_FILE_SIZE),
                name="resume_file_size_valid",
            ),
            models.CheckConstraint(
                condition=models.Q(version__gte=1), name="resume_version_positive"
            ),
        ]
