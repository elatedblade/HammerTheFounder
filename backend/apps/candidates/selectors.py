from .models import CandidateProfile


def get_own_profile(user):
    """Return the current user's profile without creating one as a side effect."""
    return CandidateProfile.objects.filter(user=user).first()
from django.db.models import Q


def get_operational_candidates(user):
    from apps.operations.common import require_operator, administrator
    from apps.candidates.models import CandidateProfile
    require_operator(user)
    queryset = CandidateProfile.objects.filter(user__is_active=True, user__role="CLIENT").select_related("user")
    if administrator(user):
        return queryset
    return queryset.filter(Q(campaigns__assigned_to=user) | Q(campaigns__assigned_to__isnull=True, campaigns__status__in=("DRAFT", "ONBOARDING", "READY")) | Q(campaigns__isnull=True)).distinct()


def get_visible_candidate_ids(user):
    """Candidate scope to intersect with any candidate-filtered history query."""
    from apps.campaigns.selectors import get_visible_campaigns
    from apps.operations.common import operational

    if operational(user):
        return get_operational_candidates(user).values("pk")
    return get_visible_campaigns(user).values("candidate_id")
