from django.http import Http404
from rest_framework.exceptions import APIException, PermissionDenied, ValidationError


class Conflict(APIException):
    status_code = 409
    default_detail = "Duplicate record or invalid state transition."
    default_code = "operation_conflict"


def operational(user):
    return bool(user and user.is_authenticated and user.is_active and user.role in {"OPERATOR", "ADMIN", "SUPERADMIN"})


def administrator(user):
    return operational(user) and user.role in {"ADMIN", "SUPERADMIN"}


def require_operator(user):
    if not operational(user):
        raise PermissionDenied("An active operational identity is required.")


def require_admin(user):
    if not administrator(user):
        raise PermissionDenied("An administrator role is required.")


def visible_campaign(user, campaign_id):
    from apps.campaigns.selectors import get_visible_campaign
    from uuid import UUID
    try:
        UUID(str(campaign_id))
    except (ValueError, TypeError):
        raise ValidationError({"campaign": "Expected a UUID."})
    campaign = get_visible_campaign(user, campaign_id)
    if campaign is None:
        raise Http404
    return campaign


def bounded(queryset, params):
    try:
        limit = min(max(int(params.get("limit", 100)), 1), 500)
        offset = max(int(params.get("offset", 0)), 0)
    except (ValueError, TypeError):
        raise ValidationError({"limit": "Use integer pagination values."})
    return queryset[offset:offset + limit]
