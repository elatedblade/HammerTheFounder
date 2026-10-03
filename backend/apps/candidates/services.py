from django.db import transaction
from rest_framework.exceptions import APIException, PermissionDenied

from apps.users.models import User

from .models import CandidateProfile


class CandidateProfileVersionConflict(APIException):
    status_code = 409
    default_detail = "The candidate profile version is stale."
    default_code = "stale_profile_version"


def upsert_own_profile(*, user, data):
    """Create or update a profile using an optimistic version precondition.

    The user row is locked before looking up the one-to-one profile. This makes
    the first-create path deterministic under concurrent requests as well as
    serializing subsequent version checks and updates.
    """
    values = dict(data)
    expected_version = values.pop("profile_version")

    with transaction.atomic():
        locked_user = User.objects.select_for_update().get(pk=user.pk)
        if not locked_user.is_active or locked_user.role != User.Role.CLIENT:
            raise PermissionDenied("An active client role is required.")

        profile = (
            CandidateProfile.objects.select_for_update()
            .filter(user=locked_user)
            .first()
        )
        if profile is None:
            if expected_version != 0:
                raise CandidateProfileVersionConflict()
            profile = CandidateProfile.objects.create(
                user=locked_user,
                profile_version=1,
                **values,
            )
            from apps.events.services import record_event
            from apps.operations.services import state_identifiers
            record_event(actor=user, event_type="candidate.created", summary="Candidate intake created.", payload={"before": None, "after": state_identifiers(profile)}, client_visible=False)
            return profile

        if expected_version != profile.profile_version:
            raise CandidateProfileVersionConflict()
        from apps.operations.services import state_identifiers
        before = state_identifiers(profile)

        for field, value in values.items():
            setattr(profile, field, value)
        if profile.expected_ctc_min is not None and profile.expected_ctc_max is not None and profile.expected_ctc_min > profile.expected_ctc_max:
            from rest_framework.exceptions import ValidationError
            raise ValidationError({"expected_ctc_max": "Maximum must be at least the minimum."})
        if values:
            profile.review_status = "PENDING"
            profile.reviewed_at = None
            profile.reviewed_by = None
        profile.profile_version = expected_version + 1
        profile.save(
            update_fields=[*values.keys(), "profile_version", "updated_at", "review_status", "reviewed_at", "reviewed_by"],
        )
        from apps.events.services import record_event
        record_event(actor=user, event_type="candidate.updated", summary="Candidate profile updated.", payload={"candidate_id": profile.pk, "fields": sorted(values), "before": before, "after": state_identifiers(profile)}, client_visible=False)
        return profile
