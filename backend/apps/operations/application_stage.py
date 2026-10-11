"""Forward-only edits of the five customer-visible application stages."""
from django.db import transaction
from django.http import Http404
from django.utils import timezone
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.applications.stages import STAGE_STATUSES, application_stage
from apps.campaigns.models import Campaign
from apps.events.services import record_event
from apps.jobs.models import Job
from apps.users.permissions import IsOperatorOrAdmin
from .common import Conflict, require_operator, visible_campaign
from .selectors import records
from .serializers import ApplicationSerializer
from .services import ensure_workable, state_identifiers


STAGE_VALUES = {
    "SAVED": "SAVED",
    "IN_PROGRESS": "IN_PROGRESS",
    "UNDER_REVIEW": "IN_REVIEW",
    "INTERVIEWS": "INTERVIEW",
    "OFFERS": "OFFER",
}


class StrictBooleanField(serializers.BooleanField):
    def to_internal_value(self, data):
        if type(data) is not bool:
            self.fail("invalid", input=data)
        return data


class ApplicationStageSerializer(serializers.Serializer):
    stage = serializers.ChoiceField(choices=tuple(STAGE_STATUSES))
    submission_confirmed = StrictBooleanField(required=False, default=False)
    notes = serializers.CharField(required=False, allow_blank=True, max_length=10000)

    def validate(self, attrs):
        unknown = set(self.initial_data) - set(self.fields)
        if unknown:
            raise serializers.ValidationError({key: "This field is not writable." for key in unknown})
        return attrs


@transaction.atomic
def change_application_stage(*, user, object_id, stage, submission_confirmed=False, notes=None):
    require_operator(user)
    if stage not in STAGE_VALUES:
        raise serializers.ValidationError({"stage": "Choose one of the five application stages."})
    obj = records(user, "applications").filter(pk=object_id).first()
    if obj is None:
        raise Http404
    campaign = Campaign.objects.select_for_update().get(pk=obj.campaign_id)
    visible_campaign(user, campaign.pk)
    ensure_workable(campaign)
    obj = records(user, "applications").select_for_update(of=("self",)).get(pk=object_id)
    current = application_stage(obj.status)
    if current is None:
        raise Conflict("This application has a historical failure, rejection, or withdrawal. Keep this record unchanged and use the lifecycle workflow for any follow-up.")
    if stage == current:
        return obj
    order = tuple(STAGE_VALUES)
    if order.index(stage) < order.index(current):
        raise Conflict("Application stages cannot move backward after progress. Choose the current stage or a later stage; use notes to record a correction.")
    needs_submission = order.index(stage) >= order.index("UNDER_REVIEW") and obj.submitted_at is None
    if needs_submission and not submission_confirmed:
        raise Conflict("Confirm that this application was submitted before moving to Under review, Interviews, or Offers.")
    if needs_submission or (current == "SAVED" and stage == "IN_PROGRESS"):
        job = Job.objects.select_for_update().get(pk=obj.job_id)
        if campaign.status != "ACTIVE" or job.status != "OPEN":
            raise Conflict("Starting progress or confirming submission requires an active campaign and an open job.")
    before = state_identifiers(obj)
    previous = obj.status
    if needs_submission:
        obj.submitted_at = timezone.now()
    if stage == "IN_PROGRESS":
        obj.in_progress_at = obj.in_progress_at or timezone.now()
    obj.status = STAGE_VALUES[stage]
    if notes is not None:
        obj.notes = notes
    # Dates are historical facts, including an interview date when moving to Offer.
    obj.save()
    record_event(
        campaign=campaign, actor=user, event_type="applications.status_changed",
        summary=f"Application is {obj.status.lower().replace('_', ' ')}.",
        payload={"id": str(obj.pk), "from": previous, "to": obj.status,
                 "before": before, "after": state_identifiers(obj)},
    )
    return obj


class ApplicationStageView(APIView):
    permission_classes = (IsOperatorOrAdmin,)

    def post(self, request, object_id):
        serializer = ApplicationStageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        obj = change_application_stage(user=request.user, object_id=object_id, **serializer.validated_data)
        return Response(ApplicationSerializer(obj, context={"request": request}).data)
