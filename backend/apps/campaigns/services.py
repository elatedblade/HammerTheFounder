from django.db import transaction
from django.http import Http404
from django.utils import timezone
from rest_framework.exceptions import APIException

from apps.candidates.models import CandidateProfile
from apps.resumes.models import Resume
from apps.users.models import User

from .models import Campaign


class CampaignNotReady(APIException):
    status_code = 409
    default_detail = "Complete the candidate profile and upload a resume first."
    default_code = "campaign_not_ready"


class InvalidCampaignTransition(APIException):
    status_code = 409
    default_detail = "This campaign cannot make that status transition."
    default_code = "invalid_campaign_transition"


def candidate_is_campaign_ready(candidate):
    return candidate.basics_complete and candidate.resumes.filter(
        upload_status=Resume.UploadStatus.UPLOADED
    ).exists()


def create_campaign(*, candidate_id, plan, trial_end_date=None, settings_json=None):
    candidate = CandidateProfile.objects.filter(
        pk=candidate_id,
        user__role=User.Role.CLIENT,
        user__is_active=True,
    ).first()
    if candidate is None:
        raise Http404
    return Campaign.objects.create(
        candidate=candidate,
        plan=plan,
        status=(
            Campaign.Status.READY
            if candidate_is_campaign_ready(candidate)
            else Campaign.Status.DRAFT
        ),
        trial_end_date=trial_end_date,
        settings_json=settings_json or {},
    )


def _lock_campaign(campaign_id):
    campaign = (
        Campaign.objects.select_for_update()
        .select_related("candidate")
        .filter(pk=campaign_id)
        .first()
    )
    if campaign is None:
        raise Http404
    return campaign


def start_campaign(*, campaign_id):
    not_ready = False
    with transaction.atomic():
        campaign = _lock_campaign(campaign_id)
        if campaign.status not in {
            Campaign.Status.DRAFT,
            Campaign.Status.ONBOARDING,
            Campaign.Status.READY,
        }:
            raise InvalidCampaignTransition()
        if not candidate_is_campaign_ready(campaign.candidate):
            if campaign.status != Campaign.Status.ONBOARDING:
                campaign.status = Campaign.Status.ONBOARDING
                campaign.version += 1
                campaign.save(update_fields=["status", "version", "updated_at"])
            not_ready = True
        else:
            campaign.status = Campaign.Status.ACTIVE
            campaign.start_date = campaign.start_date or timezone.localdate()
            campaign.version += 1
            campaign.save(
                update_fields=["status", "start_date", "version", "updated_at"]
            )
    if not_ready:
        raise CampaignNotReady()
    return campaign


def pause_campaign(*, campaign_id):
    return _transition_campaign(
        campaign_id=campaign_id,
        expected=Campaign.Status.ACTIVE,
        target=Campaign.Status.PAUSED,
    )


def resume_campaign(*, campaign_id):
    return _transition_campaign(
        campaign_id=campaign_id,
        expected=Campaign.Status.PAUSED,
        target=Campaign.Status.ACTIVE,
    )


def _transition_campaign(*, campaign_id, expected, target):
    with transaction.atomic():
        campaign = _lock_campaign(campaign_id)
        if campaign.status != expected:
            raise InvalidCampaignTransition()
        campaign.status = target
        campaign.version += 1
        campaign.save(update_fields=["status", "version", "updated_at"])
        return campaign
