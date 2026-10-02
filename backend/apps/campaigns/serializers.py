from rest_framework import serializers

from .models import Campaign


class CampaignSerializer(serializers.ModelSerializer):
    candidate_id = serializers.IntegerField(read_only=True)

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
        )
        read_only_fields = fields


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
