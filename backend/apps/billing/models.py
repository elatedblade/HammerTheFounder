import uuid

from django.conf import settings
from django.db import models


class Payment(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING"
        VERIFIED = "VERIFIED"
        FAILED = "FAILED"
        REFUNDED = "REFUNDED"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    campaign = models.ForeignKey("campaigns.Campaign", on_delete=models.PROTECT, related_name="payments")
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default="INR")
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING)
    reference = models.CharField(max_length=128, blank=True)
    notes = models.TextField(blank=True)
    idempotency_key = models.CharField(max_length=128, null=True, blank=True, unique=True)
    verified_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.PROTECT)
    verified_at = models.DateTimeField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)
        constraints = [
            models.CheckConstraint(condition=models.Q(amount__gt=0), name="payment_positive_amount"),
            models.UniqueConstraint(fields=("reference",), condition=~models.Q(reference=""), name="payment_unique_reference"),
        ]
