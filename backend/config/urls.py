"""URL configuration for the backend."""

from django.http import JsonResponse
from django.urls import include, path
from django.views.decorators.http import require_GET


@require_GET
def health(request):
    """Return a lightweight liveness response without touching dependencies."""
    return JsonResponse({"status": "ok"})


urlpatterns = [
    path("health/", health, name="health"),
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
