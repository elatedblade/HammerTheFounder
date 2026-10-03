from django.db import transaction
from django.utils import timezone
from apps.campaigns.models import Campaign
from apps.events.services import record_event


def expire_trials(*, as_of=None, limit=500):
    """Pause unpaid expired trials. Repeat runs do not duplicate events.

    Date-only trials remain valid through trial_end_date in the Django timezone.
    This does not send reminders or charge a customer.
    """
    as_of = as_of or timezone.localdate()
    ids = list(Campaign.objects.filter(trial_end_date__lt=as_of, status="ACTIVE").exclude(billing_status="ACTIVE").values_list("pk", flat=True)[:limit])
    count = 0
    for pk in ids:
        with transaction.atomic():
            campaign = Campaign.objects.select_for_update().get(pk=pk)
            if campaign.status != "ACTIVE" or campaign.billing_status == "ACTIVE" or not campaign.trial_end_date or campaign.trial_end_date >= as_of:
                continue
            campaign.status = "PAUSED"
            campaign.billing_status = "PAST_DUE"
            campaign.version += 1
            campaign.save(update_fields=["status", "billing_status", "version", "updated_at"])
            record_event(campaign=campaign, event_type="TRIAL_EXPIRED", summary="Unpaid trial expired; campaign paused.", payload={"trial_end_date": campaign.trial_end_date.isoformat()})
            count += 1
    return count
