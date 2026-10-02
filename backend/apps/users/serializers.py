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
