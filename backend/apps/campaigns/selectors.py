from .models import Campaign


def get_visible_campaigns(user):
    if user.role in {"OPERATOR", "ADMIN", "SUPERADMIN"}:
        return Campaign.objects.select_related("candidate", "candidate__user")
    return Campaign.objects.filter(candidate__user=user).select_related(
        "candidate", "candidate__user"
    )


def get_visible_campaign(user, campaign_id):
    return get_visible_campaigns(user).filter(pk=campaign_id).first()
