from django.db import transaction
from rest_framework.exceptions import APIException, PermissionDenied

from apps.candidates.models import CandidateProfile
from apps.integrations.storage.s3 import get_resume_storage
from apps.users.models import User

from .constants import CONTENT_TYPE_EXTENSIONS, UPLOAD_URL_EXPIRY_SECONDS
from .models import Resume


class CandidateProfileRequired(APIException):
    status_code = 409
    default_detail = "Save your candidate profile before uploading a resume."
    default_code = "candidate_profile_required"


def authorize_own_resume_upload(*, user, data):
    if not user.is_authenticated or not user.is_active or user.role != User.Role.CLIENT:
        raise PermissionDenied("An active client role is required.")

    # Check configuration first. No AWS client or metadata record is created if
    # storage is unconfigured, regardless of whether a profile has been saved.
    storage = get_resume_storage()
    candidate = CandidateProfile.objects.filter(user=user).first()
    if candidate is None:
        raise CandidateProfileRequired()

    resume = Resume(
        candidate=candidate,
        original_filename=data["filename"],
        content_type=data["content_type"],
        file_size=data["file_size"],
    )
    extension = CONTENT_TYPE_EXTENSIONS[resume.content_type]
    resume.s3_key = f"candidates/{candidate.pk}/resumes/{resume.pk}/original{extension}"

    with transaction.atomic():
        resume.save()
        upload = storage.authorize_upload(
            key=resume.s3_key,
            content_type=resume.content_type,
            file_size=resume.file_size,
            expires_in=UPLOAD_URL_EXPIRY_SECONDS,
        )
    return resume, upload
