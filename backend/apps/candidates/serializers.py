from rest_framework import serializers

from .models import CandidateProfile


class CandidateProfileSerializer(serializers.ModelSerializer):
    basics_complete = serializers.SerializerMethodField(read_only=True)
    profile_version = serializers.IntegerField(min_value=0, required=True)
    expected_ctc_min = serializers.DecimalField(max_digits=14, decimal_places=2, required=False, allow_null=True, min_value=0, coerce_to_string=False)
    expected_ctc_max = serializers.DecimalField(max_digits=14, decimal_places=2, required=False, allow_null=True, min_value=0, coerce_to_string=False)

    class Meta:
        model = CandidateProfile
        fields = (
            "id",
            "full_name",
            "headline",
            "location",
            "experience_summary",
            "target_roles",
            "preferred_locations",
            "remote_preference",
            "target_industries", "expected_ctc_min", "expected_ctc_max",
            "work_authorization", "sponsorship_requirement", "notice_period",
            "preferences_json", "review_status",
            "profile_version",
            "created_at",
            "updated_at",
            "basics_complete",
        )
        read_only_fields = (
            "id",
            "created_at",
            "updated_at",
            "basics_complete",
            "review_status",
        )

    def to_internal_value(self, data):
        allowed = set(self.fields)
        immutable = set(self.Meta.read_only_fields) | {
            "owner",
            "user",
            "status",
        }
        errors = {}
        for key in data.keys():
            if key not in allowed:
                errors[key] = "This field is not writable."
            elif key in immutable:
                errors[key] = "This field is read-only."
        if errors:
            raise serializers.ValidationError(errors)
        return super().to_internal_value(data)

    def validate(self, attrs):
        # DRF's partial mode normally skips required fields; the version is an
        # explicit compare-and-swap precondition and is required on every PATCH.
        if "profile_version" not in self.initial_data:
            raise serializers.ValidationError(
                {"profile_version": "This field is required."}
            )
        low = attrs.get("expected_ctc_min", getattr(self.instance, "expected_ctc_min", None))
        high = attrs.get("expected_ctc_max", getattr(self.instance, "expected_ctc_max", None))
        if (low is not None and low < 0) or (high is not None and high < 0):
            raise serializers.ValidationError({"expected_ctc_min": "Compensation must not be negative."})
        if low is not None and high is not None and low > high:
            raise serializers.ValidationError({"expected_ctc_max": "Maximum must be at least the minimum."})
        if "preferences_json" in attrs and not isinstance(attrs["preferences_json"], dict):
            raise serializers.ValidationError({"preferences_json": "Expected an object."})
        return attrs

    def validate_full_name(self, value):
        return value.strip()

    def validate_headline(self, value):
        return value.strip()

    def validate_location(self, value):
        return value.strip()

    def validate_experience_summary(self, value):
        return value.strip()

    def _validate_string_list(self, value):
        if not isinstance(value, list):
            raise serializers.ValidationError("Expected a list of strings.")
        if len(value) > 10:
            raise serializers.ValidationError("A maximum of 10 values is allowed.")
        normalized = []
        for item in value:
            if not isinstance(item, str):
                raise serializers.ValidationError("Every value must be a string.")
            item = item.strip()
            if not item:
                raise serializers.ValidationError("Values must not be empty.")
            if len(item) > 100:
                raise serializers.ValidationError(
                    "Each value must be at most 100 characters."
                )
            normalized.append(item)
        if len(set(normalized)) != len(normalized):
            raise serializers.ValidationError("Values must be distinct.")
        return normalized

    def validate_target_roles(self, value):
        return self._validate_string_list(value)

    def validate_preferred_locations(self, value):
        return self._validate_string_list(value)

    def validate_target_industries(self, value):
        return self._validate_string_list(value)

    def get_basics_complete(self, obj):
        return obj.basics_complete
