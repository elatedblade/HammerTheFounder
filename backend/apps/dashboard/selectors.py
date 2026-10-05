from django.db.models import Count, Q
from apps.campaigns.selectors import get_visible_campaigns
from apps.operations.common import visible_campaign, operational
from apps.applications.models import Application
from apps.applications.stages import stage_counts
from apps.outreach.models import Outreach
from apps.outreach.stages import stage_counts as outreach_stage_counts
from apps.tasks.models import HumanTask
from apps.billing.models import Payment
from django.utils import timezone


SUBMITTED_APPLICATION_STATUSES = (
    "SUBMITTED", "IN_REVIEW", "RECRUITER_CONTACTED", "INTERVIEW",
    "INTERVIEW_SCHEDULED", "OFFER", "REJECTED",
)


def submitted_application_q(prefix=""):
    """The canonical evidence that an application was sent externally."""
    return Q(**{prefix + "submitted_at__isnull": False}) | Q(
        **{prefix + "status__in": SUBMITTED_APPLICATION_STATUSES}
    )


def campaign_metrics(user, campaign_id=None):
    campaigns = get_visible_campaigns(user)
    if campaign_id:
        visible_campaign(user, campaign_id)
        campaigns = campaigns.filter(pk=campaign_id)
    applications = Application.objects.filter(campaign__in=campaigns)
    outreach = Outreach.objects.filter(campaign__in=campaigns)
    app_counts = {row["status"]: row["total"] for row in applications.values("status").annotate(total=Count("id"))}
    out_counts = {row["status"]: row["total"] for row in outreach.values("status").annotate(total=Count("id"))}
    out_stages = outreach_stage_counts(out_counts)
    return {
        "applications": {
            "total": sum(app_counts.values()), "submitted": applications.filter(submitted_application_q()).count(),
            "in_review": app_counts.get("IN_REVIEW", 0) + app_counts.get("RECRUITER_CONTACTED", 0), "interviews": app_counts.get("INTERVIEW", 0) + app_counts.get("INTERVIEW_SCHEDULED", 0),
            "offers": app_counts.get("OFFER", 0), "rejected": app_counts.get("REJECTED", 0),
            "queued": app_counts.get("QUEUED", 0), "in_progress": app_counts.get("IN_PROGRESS", 0),
            "failed": app_counts.get("APPLICATION_FAILED", 0), "interview_scheduled": app_counts.get("INTERVIEW_SCHEDULED", 0),
            "upcoming_interviews": applications.filter(status="INTERVIEW_SCHEDULED", interview_scheduled_at__gte=timezone.now()).count(),
            "by_status": {status: app_counts.get(status, 0) for status in Application.Status.values},
            "stage_counts": stage_counts(app_counts),
        },
        "outreach": {
            "total": sum(out_counts.values()), "sent": out_stages["SENT"],
            "replies": out_stages["RESPONDED"],
            # Keep older clients using `replies` and newer `replied` consumers aligned.
            "replied": out_stages["RESPONDED"], "positive_replies": out_counts.get("POSITIVE_REPLY", 0),
            "bounced": out_counts.get("BOUNCED", 0),
            "delivered": out_counts.get("DELIVERED", 0), "negative_replies": out_counts.get("NEGATIVE_REPLY", 0),
            # Lifetime evidence deliberately overlaps current stages and outcomes.
            "sent_lifetime": outreach.filter(Q(sent_at__isnull=False) | Q(status__in=("SENT", "DELIVERED", "REPLIED", "POSITIVE_REPLY", "NEGATIVE_REPLY", "BOUNCED"))).count(),
            "replied_lifetime": outreach.filter(Q(reply_at__isnull=False) | Q(status__in=("REPLIED", "POSITIVE_REPLY", "NEGATIVE_REPLY"))).count(),
            "delivered_lifetime": outreach.filter(Q(delivered_at__isnull=False) | Q(status="DELIVERED")).count(),
            "review_required": out_counts.get("REVIEW_REQUIRED", 0),
            "by_status": {status: out_counts.get(status, 0) for status in Outreach.Status.values},
            "stage_counts": out_stages,
        },
        "campaigns": {"total": campaigns.count(), "active": campaigns.filter(status="ACTIVE").count(), "ready": campaigns.filter(status="READY").count()},
        "payments": {"pending": Payment.objects.filter(campaign__in=campaigns, status="PENDING").count()},
        "tasks": {"open": HumanTask.objects.filter(campaign__in=campaigns, status__in=("OPEN", "CLAIMED")).count() if operational(user) else 0},
    }
