import hashlib
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode
from django.db import IntegrityError, transaction
from django.http import Http404
from django.utils import timezone
from rest_framework.exceptions import ValidationError, PermissionDenied
from apps.events.services import record_event
from apps.users.models import User
from apps.applications.stages import TRANSITION_ALIASES
from apps.operations.common import Conflict, require_operator, require_admin, administrator, visible_campaign
from .selectors import records, MODELS


def canonical_url(value):
    if not value:
        return ""
    parsed = urlsplit(value.strip())
    query = sorted((k, v) for k, v in parse_qsl(parsed.query) if not k.lower().startswith("utm_") and k.lower() not in {"fbclid", "gclid"})
    return urlunsplit((parsed.scheme.lower(), parsed.netloc.lower(), parsed.path.rstrip("/") or "/", urlencode(query), ""))


def identity(values):
    return hashlib.sha256("|".join(str(v).strip().casefold() for v in values).encode()).hexdigest()


def assignee(user_id):
    if user_id is None:
        return None
    user = User.objects.filter(pk=user_id, is_active=True, role__in=("OPERATOR", "ADMIN", "SUPERADMIN")).first()
    if user is None:
        raise ValidationError({"assigned_to": "Choose an active operator or administrator."})
    return user


def ensure_workable(campaign):
    if campaign.status in {"COMPLETED", "CANCELLED"}:
        raise Conflict("This campaign is closed.")


def state_identifiers(obj):
    """Safe audit snapshot: IDs and state only, never message/profile content."""
    if obj is None:
        return None
    fields = ("status", "campaign_id", "candidate_id", "job_id", "contact_id", "company_id", "assigned_to_id", "priority", "plan", "review_status", "version", "profile_version", "interview_scheduled_at")
    values = {"id": str(obj.pk)}
    for field in fields:
        if hasattr(obj, field):
            value = getattr(obj, field)
            values[field] = value.isoformat() if hasattr(value, "isoformat") else str(value) if field.endswith("_id") and value is not None else value
    return values


def review_task(*, campaign, entity, task_type, actor, priority=3):
    """Called under the campaign lock; deduplicate outstanding human work."""
    from apps.tasks.models import HumanTask
    reference = {"entity_type": entity._meta.label_lower, "entity_id": str(entity.pk)}
    task = campaign.human_tasks.filter(task_type=task_type, status__in=("OPEN", "CLAIMED"), payload_json__entity_id=reference["entity_id"]).first()
    if task is None:
        task = HumanTask.objects.create(campaign=campaign, task_type=task_type, priority=priority, assigned_to=campaign.assigned_to, payload_json=reference)
        record_event(campaign=campaign, actor=actor, event_type="tasks.created", summary="Human review task created.", payload={"before": None, "after": state_identifiers(task), **reference}, client_visible=False)
    return task


def validate_interview_date(value):
    if value is not None and (timezone.is_naive(value) or value <= timezone.now()):
        raise ValidationError({"interview_scheduled_at": "Use a future timezone-aware datetime."})


def prepare(kind, data, instance=None):
    values = dict(data)
    if "assigned_to_id" in values:
        values["assigned_to"] = values.pop("assigned_to_id")
    def current(key, default=""):
        return values.get(key, getattr(instance, key, default))
    if kind == "companies":
        website = canonical_url(current("website"))
        values["website"] = website
        host = urlsplit(website).hostname or ""
        values["identity_key"] = ("domain:" + host.removeprefix("www.")) if host else "name:" + current("name").strip().casefold()
    if kind == "jobs":
        url = canonical_url(current("canonical_url"))
        values["canonical_url"] = url
        company = current("company", None)
        source, external_id = current("external_source"), current("external_id")
        values["identity_key"] = identity(("url", url) if url else (("source", source, external_id) if source and external_id else (company.pk, current("title"), current("location"))))
    if kind == "contacts":
        email = current("email").strip().lower()
        profile = canonical_url(current("profile_url"))
        values.update(email=email, profile_url=profile)
        company = current("company", None)
        values["identity_key"] = identity((company.pk, "email", email) if email else ((company.pk, "profile", profile) if profile else (company.pk, "name", current("name"))))
    return values


def _write(*, user, kind, data, object_id=None):
    require_operator(user)
    with transaction.atomic():
        instance = None
        if object_id:
            instance = records(user, kind).filter(pk=object_id).first()
            if instance is None:
                raise Http404
            if kind not in {"applications", "outreach", "tasks"}:
                instance = records(user, kind).select_for_update(of=("self",)).get(pk=object_id)
        values = prepare(kind, data, instance)
        before = state_identifiers(instance)
        if kind in {"applications", "outreach", "tasks"}:
            if instance and {"campaign", "job", "contact", "channel", "task_type", "payload_json"}.intersection(values):
                allowed = {"payload_json"} if kind == "tasks" else set()
                forbidden = set(values) & ({"campaign", "job", "contact", "channel", "task_type", "payload_json"} - allowed)
                if forbidden:
                    raise ValidationError({key: "This relationship is immutable." for key in forbidden})
            campaign = instance.campaign if instance else values.get("campaign")
            campaign = visible_campaign(user, campaign.pk)
            # Campaign lock serializes writes against completion/assignment.
            from apps.campaigns.models import Campaign
            campaign = Campaign.objects.select_for_update().get(pk=campaign.pk)
            visible_campaign(user, campaign.pk)
            ensure_workable(campaign)
            if instance:
                instance = records(user, kind).select_for_update(of=("self",)).get(pk=object_id)
                before = state_identifiers(instance)
            if kind == "applications":
                if "interview_scheduled_at" in values:
                    value = values["interview_scheduled_at"]
                    validate_interview_date(value)
                    if not instance or instance.status not in {"INTERVIEW", "INTERVIEW_SCHEDULED"}:
                        raise Conflict("An interview date can only be edited in an interview state.")
                    if instance.status == "INTERVIEW_SCHEDULED" and value is None:
                        raise ValidationError({"interview_scheduled_at": "Scheduled interviews require a date."})
                from apps.jobs.models import Job
                job = Job.objects.select_for_update().get(pk=instance.job_id if instance else values["job"].pk)
                if not instance:
                    values["job"] = job
            if kind == "applications" and not instance and values["job"].status != "OPEN":
                raise Conflict("Applications can only be saved for open jobs.")
            if kind == "outreach":
                if instance and instance.status not in {"DRAFT", "READY", "TARGET_IDENTIFIED", "CONTACT_VERIFIED", "DRAFTED", "REVIEW_REQUIRED"} and {"subject", "body"}.intersection(values):
                    raise Conflict("Sent message content is immutable.")
                contact = instance.contact if instance else values["contact"]
                from apps.contacts.models import Contact
                contact = Contact.objects.select_for_update().get(pk=contact.pk)
                from apps.outreach.models import Suppression
                if contact.email and Suppression.objects.filter(email=contact.email.lower()).exists():
                    raise Conflict("This contact is suppressed.")
            if kind == "tasks":
                if instance and instance.status in {"COMPLETED", "CANCELLED"}:
                    raise Conflict("This task is closed.")
                if "assigned_to" in values:
                    require_admin(user)
                    target = assignee(values.pop("assigned_to"))
                    if target and not administrator(target) and campaign.assigned_to_id not in {None, target.pk}:
                        raise ValidationError({"assigned_to": "The operator must own the campaign."})
                    values["assigned_to"] = target
                if instance:
                    require_admin(user)
                    if set(values) - {"assigned_to", "priority"}:
                        raise ValidationError("Only assignment and priority can be edited.")
        if kind == "suppression":
            # Same contact lock as outreach transition closes suppression/send races.
            from apps.contacts.models import Contact
            list(Contact.objects.select_for_update().filter(email=values["email"]).order_by("pk"))
        if instance:
            for key, value in values.items():
                setattr(instance, key, value)
            instance.save()
            obj = instance
        else:
            obj = MODELS[kind].objects.create(**values)
        campaign = getattr(obj, "campaign", None)
        record_event(campaign=campaign, actor=user, event_type=f"{kind}.{'updated' if instance else 'created'}", summary=f"{kind.replace('_', ' ').capitalize()} {'updated' if instance else 'created'}.", payload={"id": str(obj.pk), "fields": sorted(data), "before": before, "after": state_identifiers(obj)}, client_visible=kind in {"applications", "outreach"})
        if not instance and kind in {"applications", "outreach"}:
            review_task(campaign=campaign, entity=obj, task_type="APPLICATION_FIT_REVIEW" if kind == "applications" else "CONTACT_VERIFICATION", actor=user)
        if kind == "applications" and instance and obj.status == "INTERVIEW_SCHEDULED" and "interview_scheduled_at" in values:
            review_task(campaign=campaign, entity=obj, task_type="INTERVIEW_CONFIRMATION", actor=user, priority=1)
        return obj


def write_record(*, user, kind, data, object_id=None):
    try:
        return _write(user=user, kind=kind, data=data, object_id=object_id)
    except IntegrityError:
        raise Conflict("This record already exists.")


APPLICATION_TRANSITIONS = {
    # Explicitly recording a confirmed external submission need not replay
    # preparation states. The submission guards below still apply.
    "SAVED": {"DISCOVERED", "SHORTLISTED", "READY", "IN_PROGRESS", "SUBMITTED", "WITHDRAWN"},
    "DISCOVERED": {"SHORTLISTED", "IN_PROGRESS", "SUBMITTED", "WITHDRAWN"},
    "SHORTLISTED": {"QUEUED", "READY", "IN_PROGRESS", "SUBMITTED", "WITHDRAWN"},
    "QUEUED": {"IN_PROGRESS", "WITHDRAWN"},
    "IN_PROGRESS": {"SUBMITTED", "APPLICATION_FAILED", "WITHDRAWN"},
    "APPLICATION_FAILED": {"QUEUED", "WITHDRAWN"},
    "READY": {"QUEUED", "IN_PROGRESS", "SUBMITTED", "WITHDRAWN"},
    "SUBMITTED": {"IN_REVIEW", "RECRUITER_CONTACTED", "INTERVIEW", "OFFER", "REJECTED", "WITHDRAWN"},
    "IN_REVIEW": {"RECRUITER_CONTACTED", "INTERVIEW", "OFFER", "REJECTED", "WITHDRAWN"},
    "RECRUITER_CONTACTED": {"INTERVIEW", "OFFER", "REJECTED", "WITHDRAWN"},
    "INTERVIEW": {"INTERVIEW_SCHEDULED", "OFFER", "REJECTED", "WITHDRAWN"},
    "INTERVIEW_SCHEDULED": {"INTERVIEW", "OFFER", "REJECTED", "WITHDRAWN"},
    "OFFER": {"WITHDRAWN"},
    "REJECTED": set(), "WITHDRAWN": set(),
}
OUTREACH_TRANSITIONS = {
    # Recording external outreach need not replay preparation states.
    "DRAFT": {"TARGET_IDENTIFIED", "CONTACT_VERIFIED", "DRAFTED", "REVIEW_REQUIRED", "READY", "SENT", "CLOSED", "SUPPRESSED"},
    "TARGET_IDENTIFIED": {"CONTACT_VERIFIED", "SENT", "CLOSED", "SUPPRESSED"},
    "CONTACT_VERIFIED": {"DRAFTED", "DRAFT", "SENT", "CLOSED", "SUPPRESSED"},
    "DRAFTED": {"REVIEW_REQUIRED", "SENT", "CLOSED", "SUPPRESSED"},
    "REVIEW_REQUIRED": {"DRAFTED", "READY", "SENT", "CLOSED", "SUPPRESSED"},
    "READY": {"DRAFT", "REVIEW_REQUIRED", "SENT", "CLOSED", "SUPPRESSED"},
    "SENT": {"DELIVERED", "REPLIED", "POSITIVE_REPLY", "NEGATIVE_REPLY", "BOUNCED", "CLOSED", "SUPPRESSED"},
    "DELIVERED": {"REPLIED", "POSITIVE_REPLY", "NEGATIVE_REPLY", "BOUNCED", "CLOSED", "SUPPRESSED"},
    "REPLIED": {"POSITIVE_REPLY", "NEGATIVE_REPLY", "CLOSED", "SUPPRESSED"},
    "POSITIVE_REPLY": {"CLOSED", "SUPPRESSED"},
    "NEGATIVE_REPLY": {"CLOSED", "SUPPRESSED"},
    "BOUNCED": {"CLOSED", "SUPPRESSED"},
    "CLOSED": set(), "SUPPRESSED": set(),
}


@transaction.atomic
def transition_record(*, user, kind, object_id, status, notes=None, interview_scheduled_at=None):
    require_operator(user)
    if kind == "applications":
        status = TRANSITION_ALIASES.get(status, status)
    obj = records(user, kind).filter(pk=object_id).first()
    if obj is None:
        raise Http404
    from apps.campaigns.models import Campaign
    campaign = Campaign.objects.select_for_update().get(pk=obj.campaign_id)
    visible_campaign(user, campaign.pk)
    ensure_workable(campaign)
    obj = records(user, kind).select_for_update(of=("self",)).get(pk=object_id)
    before = state_identifiers(obj)
    transitions = APPLICATION_TRANSITIONS if kind == "applications" else OUTREACH_TRANSITIONS
    if status not in transitions.get(obj.status, set()):
        raise Conflict("This status transition is not allowed.")
    if interview_scheduled_at is not None and (kind != "applications" or status != "INTERVIEW_SCHEDULED"):
        raise ValidationError({"interview_scheduled_at": "Only an interview scheduling transition accepts this field."})
    if kind == "applications" and status in {"IN_PROGRESS", "SUBMITTED"}:
        from apps.jobs.models import Job
        job = Job.objects.select_for_update().get(pk=obj.job_id)
        # All currently marketed plans include applications. COLD_APPLY is the
        # stable legacy identifier for Better Apply, not an outreach-only plan.
        if campaign.status != "ACTIVE" or job.status != "OPEN":
            raise Conflict("Submission requires an active application campaign and an open job.")
        if status == "SUBMITTED":
            obj.submitted_at = obj.submitted_at or timezone.now()
        else:
            obj.in_progress_at = timezone.now()
    if kind == "applications" and status == "APPLICATION_FAILED":
        if not notes or not notes.strip():
            raise ValidationError({"notes": "Explain the application failure for human review."})
        obj.failed_at = timezone.now()
        obj.failure_reason = notes.strip()
    if kind == "applications" and status == "INTERVIEW_SCHEDULED":
        date = interview_scheduled_at or obj.interview_scheduled_at
        if date is None:
            raise ValidationError({"interview_scheduled_at": "Provide the scheduled interview datetime."})
        validate_interview_date(date)
        obj.interview_scheduled_at = date
    if kind == "applications" and obj.status == "INTERVIEW_SCHEDULED" and status == "INTERVIEW":
        obj.interview_scheduled_at = None
    if kind == "outreach":
        from apps.contacts.models import Contact
        from apps.outreach.models import Suppression
        contact = Contact.objects.select_for_update().get(pk=obj.contact_id)
        if status in {"CONTACT_VERIFIED", "DRAFTED", "REVIEW_REQUIRED", "READY", "SENT"}:
            if contact.email and Suppression.objects.filter(email=contact.email.lower()).exists():
                raise Conflict("This contact is suppressed.")
            if status != "SENT" and ((obj.channel == "EMAIL" and not contact.email) or (obj.channel == "LINKEDIN" and not contact.profile_url)):
                raise Conflict("A valid channel recipient is required.")
            if status != "CONTACT_VERIFIED" and not obj.body.strip():
                raise Conflict("Message content is required." if status == "SENT" else "Message content and a valid channel recipient are required.")
        if status == "SENT":
            # Record a manually sent message; no outbound dispatch occurs here.
            # Every plan includes outreach, including Normal Apply cold emails.
            if campaign.status != "ACTIVE":
                raise Conflict("Sending requires an active outreach campaign.")
            obj.sent_at = obj.sent_at or timezone.now()
        if status == "DELIVERED":
            obj.delivered_at = timezone.now()
        if status == "BOUNCED":
            if not notes or not notes.strip():
                raise ValidationError({"notes": "Explain the bounce for human review."})
            obj.bounced_at = timezone.now()
        if status in {"REPLIED", "POSITIVE_REPLY", "NEGATIVE_REPLY"}:
            obj.reply_at = obj.reply_at or timezone.now()
    previous = obj.status
    obj.status = status
    if notes is not None:
        obj.notes = notes
    obj.save()
    record_event(campaign=campaign, actor=user, event_type=f"{kind}.status_changed", summary=f"{'Application' if kind == 'applications' else 'Outreach'} is {status.lower().replace('_', ' ')}.", payload={"id": str(obj.pk), "from": previous, "to": status, "before": before, "after": state_identifiers(obj)})
    task_types = {"APPLICATION_FAILED": ("APPLICATION_FAILURE_REVIEW", 1), "INTERVIEW_SCHEDULED": ("INTERVIEW_CONFIRMATION", 1), "REVIEW_REQUIRED": ("OUTREACH_REVIEW", 3), "BOUNCED": ("OUTREACH_FAILURE_REVIEW", 1)}
    if status in task_types:
        task_type, priority = task_types[status]
        review_task(campaign=campaign, entity=obj, task_type=task_type, priority=priority, actor=user)
    if kind == "outreach" and status == "READY":
        review_task(campaign=campaign, entity=obj, task_type="OUTREACH_REVIEW", actor=user)
    return obj


@transaction.atomic
def task_action(*, user, object_id, action, notes=""):
    require_operator(user)
    task = records(user, "tasks").filter(pk=object_id).first()
    if task is None:
        raise Http404
    from apps.campaigns.models import Campaign
    campaign = Campaign.objects.select_for_update().get(pk=task.campaign_id)
    visible_campaign(user, campaign.pk)
    ensure_workable(campaign)
    task = records(user, "tasks").select_for_update(of=("self",)).get(pk=object_id)
    before = state_identifiers(task)
    if action == "claim":
        if task.status != "OPEN" or task.assigned_to_id not in {None, user.pk}:
            raise Conflict("This task is already assigned or closed.")
        task.assigned_to = user
        task.status = "CLAIMED"
    elif action == "complete":
        if task.status != "CLAIMED":
            raise Conflict("Claim this task before completing it.")
        if task.assigned_to_id != user.pk and not administrator(user):
            raise PermissionDenied("Only the assignee may complete this task.")
        task.status = "COMPLETED"
        task.completed_at = timezone.now()
        task.completion_notes = notes
    else:
        raise ValidationError("Unknown task action.")
    task.save()
    record_event(campaign=campaign, actor=user, event_type=f"task.{action}", summary=f"Task {action}.", payload={"id": str(task.pk), "before": before, "after": state_identifiers(task)}, client_visible=False)
    return task
