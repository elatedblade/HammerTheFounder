"""Current outreach card groups; historical outcomes are outside active stages."""

STAGE_STATUSES = {
    "SENT": ("SENT", "DELIVERED"),
    "RESPONDED": ("REPLIED", "POSITIVE_REPLY", "NEGATIVE_REPLY"),
}


def stage_counts(by_status):
    return {
        stage: sum(by_status.get(status, 0) for status in statuses)
        for stage, statuses in STAGE_STATUSES.items()
    }
