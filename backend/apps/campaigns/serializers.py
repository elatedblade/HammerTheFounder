from rest_framework import serializers

from .models import Campaign


class CampaignSerializer(serializers.ModelSerializer):
    candidate_id = serializers.IntegerField(read_only=True)
    candidate_name = serializers.CharField(source="candidate.full_name", read_only=True)
    candidate_email = serializers.CharField(source="candidate.user.email", read_only=True)

    class Meta:
        model = Campaign
        fields = (
            "id",
            "candidate_id",
            "plan",
            "status",
            "start_date",
            "trial_end_date",
            "billing_status",
            "settings_json",
            "version",
            "created_at",
            "updated_at",
            "candidate_name", "candidate_email", "assigned_to",
        )
        read_only_fields = fields

    def to_representation(self, instance):
        data = super().to_representation(instance)
        user = self.context.get("request").user if self.context.get("request") else None
        if user and user.role == "CLIENT":
            for key in ("candidate_name", "candidate_email", "assigned_to"):
                data.pop(key, None)
            data["settings_json"] = {}
        return data


class CampaignUpdateSerializer(serializers.Serializer):
    plan = serializers.ChoiceField(choices=Campaign.Plan.choices, required=False)
    trial_end_date = serializers.DateField(required=False, allow_null=True)
    settings_json = serializers.JSONField(required=False)
    assigned_to = serializers.IntegerField(required=False, allow_null=True, min_value=1)

    def validate(self, attrs):
        unknown = set(self.initial_data) - set(self.fields)
        if unknown:
            raise serializers.ValidationError({key: "This field is not writable." for key in unknown})
        if "settings_json" in attrs and not isinstance(attrs["settings_json"], dict):
            raise serializers.ValidationError({"settings_json": "Expected an object."})
        return attrs


class CampaignCreateSerializer(serializers.Serializer):
    candidate_id = serializers.IntegerField(min_value=1)
    plan = serializers.ChoiceField(choices=Campaign.Plan.choices)
    trial_end_date = serializers.DateField(required=False, allow_null=True)
    settings_json = serializers.JSONField(required=False)

    def to_internal_value(self, data):
        allowed = set(self.fields)
        errors = {
            key: "This field is not writable."
            for key in data
            if key not in allowed
        }
        if errors:
            raise serializers.ValidationError(errors)
        values = super().to_internal_value(data)
        if "settings_json" in values and not isinstance(values["settings_json"], dict):
            raise serializers.ValidationError(
                {"settings_json": "Expected an object."}
            )
        return values
