from urllib.parse import quote
from django.conf import settings
from rest_framework import serializers
from .models import Inquiry
from .services import valid_whatsapp_number


def whatsapp_url(inquiry):
    number = getattr(settings, "WHATSAPP_BUSINESS_NUMBER", "")
    if inquiry.status not in {Inquiry.Status.OPEN, Inquiry.Status.CONTACTED} or not valid_whatsapp_number(number):
        return None
    text = f"Hello HTF, I want to discuss {Inquiry.Plan(inquiry.plan).label} (reference {inquiry.reference})."
    return f"https://wa.me/{number}?text={quote(text, safe='')}"


class InquirySerializer(serializers.ModelSerializer):
    whatsapp_url = serializers.SerializerMethodField()
    campaign_id = serializers.UUIDField(read_only=True)
    class Meta:
        model = Inquiry
        fields = ("id", "reference", "plan", "status", "created_at", "updated_at", "campaign_id", "whatsapp_url")
    def get_whatsapp_url(self, obj): return whatsapp_url(obj)


class InquiryCreateSerializer(serializers.Serializer):
    plan = serializers.ChoiceField(choices=Inquiry.Plan.choices)

    def to_internal_value(self, data):
        unknown = set(data) - {"plan"} if hasattr(data, "keys") else set()
        if unknown:
            raise serializers.ValidationError({key: "This field is not allowed." for key in unknown})
        return super().to_internal_value(data)


class InquiryAdminSerializer(InquirySerializer):
    user_id = serializers.IntegerField(read_only=True)
    candidate_id = serializers.SerializerMethodField()
    customer_name = serializers.SerializerMethodField()
    customer_email = serializers.CharField(source="user.email", read_only=True)
    notes = serializers.CharField(read_only=True)
    class Meta(InquirySerializer.Meta):
        fields = InquirySerializer.Meta.fields + ("user_id", "candidate_id", "customer_name", "customer_email", "notes")
    def get_candidate_id(self, obj):
        profile = getattr(obj.user, "candidate_profile", None)
        return profile.id if profile else None
    def get_customer_name(self, obj):
        profile = getattr(obj.user, "candidate_profile", None)
        return profile.full_name if profile else ""


class InquiryUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=Inquiry.Status.choices, required=False)
    notes = serializers.CharField(max_length=10000, required=False, allow_blank=True)

    def to_internal_value(self, data):
        unknown = set(data) - {"status", "notes"} if hasattr(data, "keys") else set()
        if unknown:
            raise serializers.ValidationError({key: "This field is not allowed." for key in unknown})
        return super().to_internal_value(data)
