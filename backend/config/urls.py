"""URL configuration for the backend."""

from django.http import JsonResponse
from django.core.cache import cache
from django.db import connection
from django.urls import include, path
from django.views.decorators.http import require_GET


@require_GET
def health(request):
    """Return a lightweight liveness response without touching dependencies."""
    return JsonResponse({"status": "ok"})


def _check_database() -> None:
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")


def _check_redis() -> None:
    """Ping the configured cache backend without including its URL in output."""
    cache_client = getattr(getattr(cache, "_cache", None), "get_client", None)
    if callable(cache_client):
        cache_client(write=True).ping()
        return

    # Local development can use Django's in-memory cache. Exercise the same
    # cache alias there so the endpoint remains useful without Redis installed.
    probe_key = "__htf_readiness_probe__"
    cache.set(probe_key, "ok", timeout=5)
    if cache.get(probe_key) != "ok":
        raise RuntimeError("cache probe failed")
    cache.delete(probe_key)


@require_GET
def readiness(request):
    """Report whether the database and configured Redis cache are reachable."""
    checks = {}
    for name, check in (("database", _check_database), ("redis", _check_redis)):
        try:
            check()
        except Exception:
            # Keep connection details, credentials, and driver errors out of
            # the public health response. Operators can inspect server logs.
            checks[name] = "error"
        else:
            checks[name] = "ok"

    ready = all(status == "ok" for status in checks.values())
    response = JsonResponse(
        {"status": "ok" if ready else "error", "checks": checks},
        status=200 if ready else 503,
    )
    response["Cache-Control"] = "no-store"
    return response


urlpatterns = [
    path("health/", health, name="health"),
    path("ready/", readiness, name="ready"),
    path("readiness/", readiness, name="readiness"),
    path("api/v1/", include("apps.users.urls")),
    path("api/v1/", include("apps.candidates.urls")),
    path("api/v1/", include("apps.resumes.urls")),
    path("api/v1/", include("apps.campaigns.urls")),
    path("api/v1/", include("apps.operations.urls")),
    path("api/v1/", include("apps.billing.urls")),
    path("api/v1/", include("apps.notifications.urls")),
    path("api/v1/", include("apps.ai.urls")),
    path("api/v1/", include("apps.inquiries.urls")),
]
