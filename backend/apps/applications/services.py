from django.db import IntegrityError, transaction
from django.http import Http404
from django.utils import timezone
from rest_framework.exceptions import APIException

from apps.campaigns.models import Campaign
from apps.jobs.models import Job

from .models import Application


class DuplicateApplication(APIException):
    status_code = 409
    default_detail = "This candidate already has an application for that job."
    default_code = "application_duplicate"


class InvalidApplicationTransition(APIException):
    status_code = 409
    default_detail = "This application cannot make that status transition."
    default_code = "invalid_application_transition"


TRANSITIONS = {
    Application.Status.DISCOVERED: {Application.Status.SHORTLISTED},
    Application.Status.SHORTLISTED: {Application.Status.QUEUED},
    Application.Status.QUEUED: {Application.Status.IN_PROGRESS},
    Application.Status.IN_PROGRESS: {
        Application.Status.SUBMITTED,
        Application.Status.APPLICATION_FAILED,
    },
    Application.Status.SUBMITTED: {Application.Status.IN_REVIEW},
    Application.Status.IN_REVIEW: {Application.Status.RECRUITER_CONTACTED},
    Application.Status.RECRUITER_CONTACTED: {Application.Status.INTERVIEW},
    Application.Status.INTERVIEW: {Application.Status.INTERVIEW_SCHEDULED},
    Application.Status.INTERVIEW_SCHEDULED: {
        Application.Status.OFFER,
        Application.Status.REJECTED,
    },
}


def _get_campaign_and_job(*, campaign_id, job_id):
    campaign = Campaign.objects.select_related("candidate").filter(pk=campaign_id).first()
    job = Job.objects.filter(pk=job_id).first()
    if campaign is None or job is None:
        raise Http404
    return campaign, job


def create_application(*, campaign_id, job_id, operator, notes="", source_reference=""):
    campaign, job = _get_campaign_and_job(campaign_id=campaign_id, job_id=job_id)
    if Application.objects.filter(candidate_id=campaign.candidate_id, job_id=job.id).exists():
        raise DuplicateApplication()
    try:
        with transaction.atomic():
            return Application.objects.create(
                campaign=campaign,
                candidate=campaign.candidate,
                job=job,
                operator=operator,
                notes=notes,
                source_reference=source_reference,
            )
    except IntegrityError as exc:
        raise DuplicateApplication() from exc


def transition_application(*, application_id, target_status, operator, notes=None):
    with transaction.atomic():
        application = (
            Application.objects.select_for_update(of=("self",))
            .select_related("campaign", "candidate", "job", "operator")
            .filter(pk=application_id)
            .first()
        )
        if application is None:
            raise Http404
        if target_status not in TRANSITIONS.get(application.status, set()):
            raise InvalidApplicationTransition()
        application.status = target_status
        application.operator = operator
        if notes is not None:
            application.notes = notes
        if target_status == Application.Status.SUBMITTED and application.submitted_at is None:
            application.submitted_at = timezone.now()
        application.save(
            update_fields=[
                "status",
                "operator",
                "notes",
                "submitted_at",
                "updated_at",
            ]
        )
        return application
