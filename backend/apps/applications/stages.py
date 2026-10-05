"""Customer-visible projections of legacy application states, never stored."""

STAGE_STATUSES = {
    "SAVED": ("SAVED", "DISCOVERED", "SHORTLISTED", "READY"),
    "IN_PROGRESS": ("QUEUED", "IN_PROGRESS"),
    "UNDER_REVIEW": ("SUBMITTED", "IN_REVIEW", "RECRUITER_CONTACTED"),
    "INTERVIEWS": ("INTERVIEW", "INTERVIEW_SCHEDULED"),
    "OFFERS": ("OFFER",),
}
STATUS_STAGES = {
    status: stage for stage, statuses in STAGE_STATUSES.items() for status in statuses
}
TRANSITION_ALIASES = {
    "UNDER_REVIEW": "IN_REVIEW",
    "INTERVIEWS": "INTERVIEW",
    "OFFERS": "OFFER",
}


def application_stage(status):
    """Failures, rejections and withdrawals remain historical outcomes."""
    return STATUS_STAGES.get(status)


def stage_counts(by_status):
    return {
        stage: sum(by_status.get(status, 0) for status in statuses)
        for stage, statuses in STAGE_STATUSES.items()
    }
