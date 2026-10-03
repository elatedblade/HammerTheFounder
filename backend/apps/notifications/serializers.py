from rest_framework import serializers
from .models import Notification, NotificationTemplate


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ("id", "campaign", "channel", "status", "subject", "body", "created_at", "sent_at")
        read_only_fields = fields


class NotificationCreateSerializer(serializers.Serializer):
    campaign = serializers.UUIDField()
    channel = serializers.ChoiceField(choices=Notification.Channel.choices)
    recipient = serializers.CharField(max_length=320)
    subject = serializers.CharField(max_length=255, required=False, allow_blank=True, default="")
    body = serializers.CharField(max_length=10000)


class TemplateSerializer(serializers.ModelSerializer):
    body = serializers.CharField(max_length=10000)

    class Meta:
        model = NotificationTemplate
        fields = ("id", "name", "channel", "subject", "body")
        read_only_fields = ("id",)
