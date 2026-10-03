from decimal import Decimal
from rest_framework import serializers
from .models import Payment


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ("id", "campaign", "amount", "currency", "status", "reference", "notes", "verified_by", "verified_at", "created_at")
        read_only_fields = fields

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if self.context["request"].user.role == "CLIENT":
            for key in ("notes", "reference", "verified_by"):
                data.pop(key, None)
        return data


class PaymentCreateSerializer(serializers.Serializer):
    campaign = serializers.UUIDField()
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal("0.01"))
    currency = serializers.ChoiceField(choices=["INR"], default="INR")
    notes = serializers.CharField(max_length=4000, required=False, allow_blank=True)


class VerifySerializer(serializers.Serializer):
    reference = serializers.CharField(max_length=128)
    notes = serializers.CharField(max_length=4000, required=False, allow_blank=True)


class TransitionSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=["FAILED", "REFUNDED"])
    notes = serializers.CharField(max_length=4000, required=False, allow_blank=True)
