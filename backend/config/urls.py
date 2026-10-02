"""URL configuration for the backend."""

from django.http import JsonResponse
from django.urls import path
from django.views.decorators.http import require_GET


@require_GET
def health(request):
    """Return a lightweight liveness response without touching dependencies."""
    return JsonResponse({"status": "ok"})


urlpatterns = [
    path("health/", health, name="health"),
]
