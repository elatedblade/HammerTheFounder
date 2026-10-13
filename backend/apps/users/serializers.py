from rest_framework import serializers

from .models import User


class CurrentUserSerializer(serializers.ModelSerializer):
    """The intentionally small identity projection exposed to frontends."""

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "phone",
            "role",
            "identity_provider",
        )
        read_only_fields = fields


class ManagedUserSerializer(serializers.ModelSerializer):
    """Safe user projection for the superadmin user-management surface."""

    clerk_subject = serializers.CharField(
        source="identity_provider_subject",
        read_only=True,
    )
    status = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "clerk_subject",
            "role",
            "status",
        )
        read_only_fields = fields

    def get_status(self, obj):
        return "ACTIVE" if obj.is_active else "INACTIVE"


class RoleChangeSerializer(serializers.Serializer):
    """Validate role changes against the application's canonical role enum."""

    role = serializers.ChoiceField(choices=User.Role.choices)
