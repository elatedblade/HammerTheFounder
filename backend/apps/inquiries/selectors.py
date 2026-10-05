from django.db.models import Q

from apps.candidates.selectors import get_operational_candidates
from apps.operations.common import administrator, require_operator

from .models import Inquiry


def operational_inquiries(user):
    """One visibility policy shared by list, detail and locked mutations."""
    require_operator(user)
    rows = Inquiry.objects.select_related("user", "user__candidate_profile", "campaign")
    if administrator(user):
        return rows
    return rows.filter(
        Q(user__candidate_profile__isnull=True)
        | Q(user_id__in=get_operational_candidates(user).values("user_id")),
        user__role="CLIENT",
        user__is_active=True,
    )
