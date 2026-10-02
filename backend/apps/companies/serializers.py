from rest_framework import serializers

from .models import Company, normalize_company_name


class CompanySerializer(serializers.ModelSerializer):
    metadata = serializers.JSONField(source="metadata_json", required=False)
    metadata_json = serializers.JSONField(required=False)

    class Meta:
        model = Company
        fields = (
            "id",
            "name",
            "normalized_name",
            "website",
            "industry",
            "location",
            "description",
            "metadata",
            "metadata_json",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "normalized_name", "created_at", "updated_at")

    def to_internal_value(self, data):
        allowed = set(self.fields)
        immutable = set(self.Meta.read_only_fields)
        errors = {}
        for key in data:
            if key not in allowed:
                errors[key] = "This field is not writable."
            elif key in immutable:
                errors[key] = "This field is read-only."
        if "metadata" in data and "metadata_json" in data:
            errors["metadata_json"] = "Use only one metadata field."
        if errors:
            raise serializers.ValidationError(errors)
        return super().to_internal_value(data)

    def validate_name(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("This field may not be blank.")
        normalized_name = normalize_company_name(value)
        queryset = Company.objects.filter(normalized_name=normalized_name)
        if self.instance is not None:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise serializers.ValidationError("A company with this name already exists.")
        return value

    def validate(self, attrs):
        metadata = attrs.get("metadata_json")
        if metadata is not None and not isinstance(metadata, dict):
            raise serializers.ValidationError({"metadata": "Expected an object."})
        return attrs
