import uuid
from django.conf import settings
from django.db import models


class Event(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    campaign = models.ForeignKey("campaigns.Campaign", null=True, blank=True, on_delete=models.CASCADE, related_name="events")
    event_type = models.CharField(max_length=100)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    summary = models.CharField(max_length=500)
    payload = models.JSONField(default=dict)
    client_visible = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at", "id")
        indexes = [models.Index(fields=("campaign", "created_at"))]
