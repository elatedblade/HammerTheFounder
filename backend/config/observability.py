"""Opt-in, privacy-first exception reporting; no request bodies or local variables."""

import os


def scrub_event(event, hint):
    for key in ("request", "user", "breadcrumbs", "extra"):
        event.pop(key, None)
    # Exception messages can contain user-provided values or provider payloads.
    for exception in event.get("exception", {}).get("values", []):
        exception["value"] = "Exception details withheld; inspect the exception type and source location."
        for frame in exception.get("stacktrace", {}).get("frames", []):
            frame.pop("vars", None)
    if "logentry" in event:
        event["logentry"] = {"message": "Application error (message withheld)."}
    return event


def configure_observability():
    dsn = os.getenv("SENTRY_DSN", "")
    if not dsn:
        return
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration
    from sentry_sdk.integrations.celery import CeleryIntegration

    sentry_sdk.init(
        dsn=dsn,
        environment=os.getenv("HTF_ENVIRONMENT", "development"),
        release=os.getenv("HTF_RELEASE") or None,
        integrations=[DjangoIntegration(), CeleryIntegration()],
        send_default_pii=False,
        include_local_variables=False,
        max_request_body_size="never",
        traces_sample_rate=0,
        before_send=scrub_event,
    )
