import unicodedata
from collections.abc import Mapping
from pathlib import PurePosixPath

from rest_framework import serializers

from .constants import CONTENT_TYPE_EXTENSIONS, MAX_RESUME_FILE_SIZE
from .models import Resume


class ResumeSerializer(serializers.ModelSerializer):
    """Metadata only: storage keys and signed URLs are never included in lists."""

    class Meta:
        model = Resume
        fields = (
            "id",
            "original_filename",
            "content_type",
            "file_size",
            "upload_status",
            "parse_status",
            "parse_error_code",
            "version",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields


class ResumeUploadRequestSerializer(serializers.Serializer):
    filename = serializers.CharField(max_length=255, trim_whitespace=False)
    content_type = serializers.ChoiceField(choices=tuple(CONTENT_TYPE_EXTENSIONS))
    file_size = serializers.IntegerField(min_value=1, max_value=MAX_RESUME_FILE_SIZE)

    def to_internal_value(self, data):
        if isinstance(data, Mapping):
            data = dict(data)
            if "filename" not in data and "original_filename" in data:
                data["filename"] = data.pop("original_filename")
            errors = {
                key: "This field is not writable."
                for key in data
                if key not in self.fields
            }
            if "file_size" in data and type(data["file_size"]) is not int:
                errors["file_size"] = "A whole number of bytes is required."
            if errors:
                raise serializers.ValidationError(errors)
        return super().to_internal_value(data)

    def validate_filename(self, value):
        # Keep only a display basename. Object keys never contain this input.
        if (
            value != value.strip()
            or value.startswith(".")
            or any(character in value for character in '/\\<>:"|?*')
            or any(unicodedata.category(character).startswith("C") for character in value)
            or len(value.encode("utf-8")) > 255
        ):
            raise serializers.ValidationError("Use a safe filename without a path.")
        return value

    def validate(self, attrs):
        suffix = PurePosixPath(attrs["filename"]).suffix.lower()
        if suffix != CONTENT_TYPE_EXTENSIONS[attrs["content_type"]]:
            raise serializers.ValidationError(
                {"filename": "The filename extension must match the content type."}
            )
        return attrs


class OperationalParsedTextSerializer(serializers.ModelSerializer):
    """Separate operational review DTO; never included in client metadata lists."""
    text = serializers.SerializerMethodField()
    truncated = serializers.SerializerMethodField()
    max_chars = serializers.SerializerMethodField()

    class Meta:
        model = Resume
        fields = ("id", "parse_status", "text", "truncated", "max_chars", "parsed_at")
        read_only_fields = fields

    def get_text(self, instance):
        return instance.extracted_text[:32000]

    def get_truncated(self, instance):
        return len(instance.extracted_text) > 32000

    def get_max_chars(self, instance):
        return 32000
