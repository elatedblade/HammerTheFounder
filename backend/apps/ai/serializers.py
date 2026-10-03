import json
from collections.abc import Mapping
from rest_framework import serializers
from .models import AIRun


class AIRunSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIRun
        fields = ("id", "campaign", "capability", "status", "result", "error_code", "created_at", "agent_version", "prompt_version", "source_references")
        read_only_fields = fields


class AIRunCreateSerializer(serializers.Serializer):
    campaign = serializers.UUIDField()
    capability = serializers.ChoiceField(choices=AIRun.Capability.choices)
    input = serializers.JSONField()

    def to_internal_value(self, data):
        if isinstance(data, Mapping):
            extra = set(data) - set(self.fields)
            if extra:
                raise serializers.ValidationError({key: "This field is not writable; use canonical capability input keys." for key in extra})
        return super().to_internal_value(data)

    def validate_input(self, value):
        if not isinstance(value, dict) or len(json.dumps(value).encode()) > 32000:
            raise serializers.ValidationError("Provide an object of at most 32KB.")
        return value
