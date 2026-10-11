from rest_framework import serializers

from apps.companies.models import Company

from .models import Job


class JobSerializer(serializers.ModelSerializer):
    company_id = serializers.PrimaryKeyRelatedField(
        source="company", queryset=Company.objects.all()
    )
    metadata = serializers.JSONField(source="metadata_json", required=False)
    metadata_json = serializers.JSONField(required=False)

    class Meta:
        model = Job
        fields = (
            "id",
            "company_id",
            "external_source",
            "external_id",
            "canonical_url",
            "title",
            "location",
            "employment_type",
            "description",
            "status",
            "fingerprint",
            "first_seen_at",
            "last_seen_at",
            "metadata",
            "metadata_json",
        )
        read_only_fields = ("id", "first_seen_at", "last_seen_at")
        validators = []

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

    def validate_external_source(self, value):
        value = value.strip().casefold()
        if not value:
            raise serializers.ValidationError("This field may not be blank.")
        return value

    def validate_external_id(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("This field may not be blank.")
        return value

    def validate_title(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("This field may not be blank.")
        return value

    def validate(self, attrs):
        source = attrs.get("external_source")
        external_id = attrs.get("external_id")
        if source is not None and external_id is not None:
            queryset = Job.objects.filter(
                external_source=source, external_id=external_id
            )
            if self.instance is not None:
                queryset = queryset.exclude(pk=self.instance.pk)
            if queryset.exists():
                raise serializers.ValidationError(
                    {"external_id": "A job with this source and ID already exists."}
                )

        metadata = attrs.get("metadata_json")
        if metadata is not None and not isinstance(metadata, dict):
            raise serializers.ValidationError({"metadata": "Expected an object."})
        return attrs
