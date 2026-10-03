from django.db import transaction
from django.http import Http404
from django.utils import timezone
from rest_framework.exceptions import APIException

from apps.candidates.models import CandidateProfile
from apps.resumes.models import Resume
from apps.users.models import User
from apps.events.services import record_event
from apps.operations.common import require_operator, require_admin, visible_campaign

from .models import Campaign


class CampaignNotReady(APIException):
    status_code = 409
    default_detail = "Complete the candidate profile, upload a resume, and obtain operator approval first."
    default_code = "campaign_not_ready"


class InvalidCampaignTransition(APIException):
    status_code = 409
    default_detail = "This campaign cannot make that status transition."
    default_code = "invalid_campaign_transition"


def candidate_is_campaign_ready(candidate):
    return candidate.basics_complete and candidate.review_status == "APPROVED" and candidate.resumes.filter(
        upload_status=Resume.UploadStatus.UPLOADED
    ).exists()


@transaction.atomic
def create_campaign(*, candidate_id, plan, trial_end_date=None, settings_json=None, actor):
    require_operator(actor)
    from apps.candidates.selectors import get_operational_candidates
    candidate = get_operational_candidates(actor).filter(
        pk=candidate_id,
        user__role=User.Role.CLIENT,
        user__is_active=True,
    ).first()
    if candidate is None:
        raise Http404
    campaign = Campaign.objects.create(
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
    from apps.operations.services import state_identifiers, review_task
    record_event(campaign=campaign, actor=actor, event_type="campaign.created", summary="Campaign created.", payload={"before": None, "after": state_identifiers(campaign)})
    if campaign.status == Campaign.Status.DRAFT:
        review_task(campaign=campaign, entity=campaign, task_type="PROFILE_CLEANUP", actor=actor, priority=4)
    return campaign


def _lock_campaign(campaign_id, actor):
    require_operator(actor)
    visible_campaign(actor, campaign_id)
    campaign = (
        Campaign.objects.select_for_update(of=("self",))
        .select_related("candidate")
        .filter(pk=campaign_id)
        .first()
    )
    if campaign is None:
        raise Http404
    visible_campaign(actor, campaign_id)
    return campaign


def start_campaign(*, campaign_id, actor):
    not_ready = False
    with transaction.atomic():
        snapshot = visible_campaign(actor, campaign_id)
        CandidateProfile.objects.select_for_update().get(pk=snapshot.candidate_id)
        campaign = _lock_campaign(campaign_id, actor)
        from apps.operations.services import state_identifiers, review_task
        before = state_identifiers(campaign)
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
            review_task(campaign=campaign, entity=campaign, task_type="PROFILE_CLEANUP", actor=actor, priority=4)
        else:
            if campaign.assigned_to_id is None and actor.role == "OPERATOR":
                from apps.operations.common import Conflict
                raise Conflict("An administrator must assign this campaign before it can start.")
            campaign.status = Campaign.Status.ACTIVE
            campaign.start_date = campaign.start_date or timezone.localdate()
            campaign.version += 1
            campaign.save(
                update_fields=["status", "start_date", "version", "updated_at"]
            )
        record_event(campaign=campaign, actor=actor, event_type="campaign.status_changed", summary=f"Campaign is {campaign.status.lower()}.", payload={"status": campaign.status, "before": before, "after": state_identifiers(campaign)})
    if not_ready:
        raise CampaignNotReady()
    return campaign


def pause_campaign(*, campaign_id, actor):
    return _transition_campaign(
        campaign_id=campaign_id,
        expected=Campaign.Status.ACTIVE,
        target=Campaign.Status.PAUSED,
        actor=actor,
    )


def resume_campaign(*, campaign_id, actor):
    return _transition_campaign(
        campaign_id=campaign_id,
        expected=Campaign.Status.PAUSED,
        target=Campaign.Status.ACTIVE,
        actor=actor,
    )


def _transition_campaign(*, campaign_id, expected, target, actor):
    with transaction.atomic():
        campaign = _lock_campaign(campaign_id, actor)
        from apps.operations.services import state_identifiers
        before = state_identifiers(campaign)
        if campaign.status not in (expected if isinstance(expected, set) else {expected}):
            raise InvalidCampaignTransition()
        campaign.status = target
        campaign.version += 1
        campaign.save(update_fields=["status", "version", "updated_at"])
        if target in {Campaign.Status.COMPLETED, Campaign.Status.CANCELLED}:
            from apps.tasks.models import HumanTask
            for task in campaign.human_tasks.select_for_update().filter(status__in=("OPEN", "CLAIMED")):
                task_before = state_identifiers(task)
                task.status = HumanTask.Status.CANCELLED
                task.save(update_fields=("status",))
                record_event(campaign=campaign, actor=actor, event_type="task.cancelled", summary="Campaign closed; pending task cancelled.", payload={"before": task_before, "after": state_identifiers(task)}, client_visible=False)
        record_event(campaign=campaign, actor=actor, event_type="campaign.status_changed", summary=f"Campaign is {target.lower()}.", payload={"status": target, "before": before, "after": state_identifiers(campaign)})
        return campaign


def complete_campaign(*, campaign_id, actor):
    return _transition_campaign(campaign_id=campaign_id, actor=actor, expected={Campaign.Status.ACTIVE, Campaign.Status.PAUSED}, target=Campaign.Status.COMPLETED)


def cancel_campaign(*, campaign_id, actor):
    return _transition_campaign(campaign_id=campaign_id, actor=actor, expected={Campaign.Status.DRAFT, Campaign.Status.ONBOARDING, Campaign.Status.READY, Campaign.Status.ACTIVE, Campaign.Status.PAUSED}, target=Campaign.Status.CANCELLED)


@transaction.atomic
def update_campaign(*, campaign_id, actor, data):
    campaign = _lock_campaign(campaign_id, actor)
    from apps.operations.services import state_identifiers
    before = state_identifiers(campaign)
    previous_assignee_id = campaign.assigned_to_id
    if campaign.status in {Campaign.Status.COMPLETED, Campaign.Status.CANCELLED}:
        raise InvalidCampaignTransition()
    values = dict(data)
    if "assigned_to" in values:
        require_admin(actor)
        target = values.pop("assigned_to")
        assignee = None
        if target is not None:
            assignee = User.objects.filter(pk=target, is_active=True, role__in=("OPERATOR", "ADMIN", "SUPERADMIN")).first()
            if assignee is None:
                from rest_framework.exceptions import ValidationError
                raise ValidationError({"assigned_to": "Choose an active operator or administrator."})
        campaign.assigned_to = assignee
    for field, value in values.items():
        setattr(campaign, field, value)
    campaign.version += 1
    campaign.save()
    if "assigned_to" in data and campaign.assigned_to_id != previous_assignee_id:
        for task in campaign.human_tasks.select_for_update().filter(status__in=("OPEN", "CLAIMED"), assigned_to_id=previous_assignee_id):
            task_before = state_identifiers(task)
            task.assigned_to = campaign.assigned_to
            task.status = "OPEN"
            task.save(update_fields=("assigned_to", "status"))
            record_event(campaign=campaign, actor=actor, event_type="task.reassigned", summary="Task ownership updated with campaign assignment.", payload={"before": task_before, "after": state_identifiers(task)}, client_visible=False)
    record_event(campaign=campaign, actor=actor, event_type="campaign.updated", summary="Campaign settings updated.", payload={"fields": sorted(data), "before": before, "after": state_identifiers(campaign)}, client_visible=False)
    return campaign
