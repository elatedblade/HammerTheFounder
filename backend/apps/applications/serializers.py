from rest_framework import serializers

from .models import Application


class ApplicationSerializer(serializers.ModelSerializer):
    campaign_id = serializers.UUIDField(read_only=True)
    job_id = serializers.UUIDField(read_only=True)
    candidate_id = serializers.IntegerField(read_only=True)
    operator_id = serializers.IntegerField(read_only=True)

    class Meta:
        model = Application
        fields = (
            "id",
            "campaign_id",
            "candidate_id",
            "job_id",
            "status",
            "submitted_at",
            "notes",
            "operator_id",
            "source_reference",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields


class ApplicationCreateSerializer(serializers.Serializer):
    campaign_id = serializers.UUIDField()
    job_id = serializers.UUIDField()
    notes = serializers.CharField(required=False, allow_blank=True)
    source_reference = serializers.CharField(required=False, allow_blank=True, max_length=2048)

    def to_internal_value(self, data):
        allowed = set(self.fields)
        errors = {
            key: "This field is not writable."
            for key in data
            if key not in allowed
        }
        if errors:
            raise serializers.ValidationError(errors)
        return super().to_internal_value(data)


class ApplicationTransitionSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=Application.Status.choices)
    notes = serializers.CharField(required=False, allow_blank=True)

    def to_internal_value(self, data):
        allowed = set(self.fields)
        errors = {
            key: "This field is not writable."
            for key in data
            if key not in allowed
        }
        if errors:
            raise serializers.ValidationError(errors)
        return super().to_internal_value(data)
