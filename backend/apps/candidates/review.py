from django.db import transaction
from django.http import Http404
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from apps.events.services import record_event
from apps.candidates.selectors import get_operational_candidates
from apps.candidates.services import CandidateProfileVersionConflict


@transaction.atomic
def review_candidate(*, actor, candidate_id, data):
    if not get_operational_candidates(actor).filter(pk=candidate_id).exists():
        raise Http404
    from apps.candidates.models import CandidateProfile
    profile = CandidateProfile.objects.select_for_update().get(pk=candidate_id)
    from apps.operations.services import state_identifiers
    before = state_identifiers(profile)
    if not get_operational_candidates(actor).filter(pk=candidate_id).exists():
        raise Http404
    values = dict(data)
    version = values.pop("profile_version", None)
    if version is not None and version != profile.profile_version:
        raise CandidateProfileVersionConflict()
    facts = set(values) - {"review_status", "review_notes"}
    for key, value in values.items():
        setattr(profile, key, value)
    if profile.expected_ctc_min is not None and profile.expected_ctc_max is not None and profile.expected_ctc_min > profile.expected_ctc_max:
        raise ValidationError({"expected_ctc_max": "Maximum must be at least the minimum."})
    if facts:
        profile.profile_version += 1
        if "review_status" not in values:
            profile.review_status = "PENDING"
            profile.reviewed_at = None
            profile.reviewed_by = None
    if "review_status" in values:
        if profile.review_status == "APPROVED":
            from apps.resumes.models import Resume
            if not profile.basics_complete or not profile.resumes.filter(upload_status=Resume.UploadStatus.UPLOADED).exists():
                raise ValidationError({"review_status": "Complete profile basics and upload a resume before approval."})
        profile.reviewed_at = timezone.now()
        profile.reviewed_by = actor
    profile.save()
    from apps.campaigns.selectors import get_visible_campaigns
    for campaign in get_visible_campaigns(actor).filter(candidate=profile):
        record_event(campaign=campaign, actor=actor, event_type="candidate.reviewed" if "review_status" in values else "candidate.updated", summary="Candidate profile reviewed." if "review_status" in values else "Candidate profile updated.", payload={"candidate_id": profile.pk, "review_status": profile.review_status, "fields": sorted(data), "before": before, "after": state_identifiers(profile)}, client_visible=False)
        if values.get("review_status") == "CHANGES_REQUESTED":
            from apps.operations.services import review_task
            from apps.campaigns.models import Campaign
            locked_campaign = Campaign.objects.select_for_update().get(pk=campaign.pk)
            if locked_campaign.status not in {"COMPLETED", "CANCELLED"}:
                review_task(campaign=locked_campaign, entity=locked_campaign, task_type="PROFILE_CLEANUP", actor=actor, priority=4)
    if not profile.campaigns.exists():
        record_event(actor=actor, event_type="candidate.updated", summary="Candidate intake reviewed.", payload={"candidate_id": profile.pk, "before": before, "after": state_identifiers(profile)}, client_visible=False)
    return profile
