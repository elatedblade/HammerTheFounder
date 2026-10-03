from django.db.models import Q
from uuid import UUID
from rest_framework.exceptions import ValidationError
from apps.campaigns.selectors import get_visible_campaigns
from apps.operations.common import require_operator, operational, administrator, visible_campaign
from apps.companies.models import Company
from apps.jobs.models import Job
from apps.applications.models import Application
from apps.contacts.models import Contact
from apps.outreach.models import Outreach, OutreachTemplate, Suppression
from apps.tasks.models import HumanTask
from apps.events.models import Event


MODELS = {"companies": Company, "jobs": Job, "applications": Application, "contacts": Contact, "outreach": Outreach, "suppression": Suppression, "templates": OutreachTemplate, "tasks": HumanTask, "events": Event, "audit": Event}
SCOPED = {"applications", "outreach", "tasks", "events", "audit"}


def records(user, kind, params=None, campaign_id=None):
    params = params or {}
    if kind not in {"applications", "outreach", "events"}:
        require_operator(user)
    queryset = MODELS[kind].objects.all()
    if kind in SCOPED:
        visible = get_visible_campaigns(user)
        if kind in {"events", "audit"} and administrator(user):
            queryset = queryset.filter(Q(campaign__in=visible) | Q(campaign__isnull=True))
        else:
            queryset = queryset.filter(campaign__in=visible)
        selected = campaign_id or params.get("campaign")
        if selected:
            try:
                selected = UUID(str(selected))
            except (ValueError, TypeError):
                raise ValidationError({"campaign": "Expected a UUID."})
            visible_campaign(user, selected)
            queryset = queryset.filter(campaign_id=selected)
    if kind == "events" and not operational(user):
        queryset = queryset.filter(client_visible=True)
    if params.get("status") and kind in {"jobs", "applications", "outreach", "tasks"}:
        queryset = queryset.filter(status=params["status"])
    if params.get("company") and kind in {"jobs", "contacts"}:
        try:
            UUID(str(params["company"]))
        except (ValueError, TypeError):
            raise ValidationError({"company": "Expected a UUID."})
        queryset = queryset.filter(company_id=params["company"])
    if params.get("q"):
        q = params["q"][:200]
        if kind == "companies":
            queryset = queryset.filter(name__icontains=q)
        if kind == "jobs":
            queryset = queryset.filter(Q(title__icontains=q) | Q(company__name__icontains=q))
        if kind == "contacts":
            queryset = queryset.filter(Q(name__icontains=q) | Q(email__icontains=q))
    related = {"jobs": ("company",), "contacts": ("company",), "applications": ("campaign", "job__company"), "outreach": ("campaign", "contact__company"), "tasks": ("campaign", "assigned_to")}
    if kind in related:
        queryset = queryset.select_related(*related[kind])
    return queryset
