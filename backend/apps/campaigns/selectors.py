from django.db.models import Q
from .models import Campaign


def get_visible_campaigns(user):
    queryset = Campaign.objects.select_related("candidate", "candidate__user", "assigned_to")
    if not user or not user.is_authenticated or not user.is_active:
        return queryset.none()
    if user.role in {"ADMIN", "SUPERADMIN"}:
        return queryset
    if user.role == "OPERATOR":
        return queryset.filter(Q(assigned_to=user) | Q(assigned_to__isnull=True, status__in=("DRAFT", "ONBOARDING", "READY")))
    return Campaign.objects.filter(candidate__user=user).select_related(
        "candidate", "candidate__user"
    )


def get_visible_campaign(user, campaign_id):
    return get_visible_campaigns(user).filter(pk=campaign_id).first()
