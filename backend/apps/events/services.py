from django.db import transaction
from .models import Event


@transaction.atomic
def record_event(*, campaign=None, event_type, actor=None, summary, payload=None, client_visible=True):
    """Append a domain event in the caller's transaction; never perform I/O."""
    from apps.audit.models import AuditEntry
    event = Event.objects.create(campaign=campaign, event_type=event_type, actor=actor, summary=summary, payload=payload or {}, client_visible=client_visible)
    AuditEntry.objects.create(event=event, actor=actor, action=event_type, payload=payload or {})
    return event
