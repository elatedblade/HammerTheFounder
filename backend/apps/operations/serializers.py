from rest_framework import serializers
from django.utils import timezone
from apps.companies.models import Company
from apps.jobs.models import Job
from apps.applications.models import Application
from apps.contacts.models import Contact
from apps.outreach.models import Outreach, OutreachTemplate, Suppression
from apps.tasks.models import HumanTask
from apps.events.models import Event
from apps.candidates.models import CandidateProfile
from apps.candidates.serializers import CandidateProfileSerializer


class StrictModelSerializer(serializers.ModelSerializer):
    def to_internal_value(self, data):
        errors = {key: "This field is not writable." for key in data if key not in self.fields or self.fields[key].read_only}
        if errors:
            raise serializers.ValidationError(errors)
        return super().to_internal_value(data)


class CompanySerializer(StrictModelSerializer):
    class Meta:
        model = Company
        fields = ("id", "name", "website", "industry", "location")
        read_only_fields = ("id",)


class JobSerializer(StrictModelSerializer):
    company_name = serializers.CharField(source="company.name", read_only=True)

    class Meta:
        model = Job
        fields = ("id", "company", "company_name", "title", "canonical_url", "external_source", "external_id", "location", "employment_type", "description", "status")
        read_only_fields = ("id",)
        # Services translate unique races and duplicate identities to 409.
        validators = []
        extra_kwargs = {"canonical_url": {"validators": []}}

    def validate(self, attrs):
        source = attrs.get("external_source", getattr(self.instance, "external_source", ""))
        external_id = attrs.get("external_id", getattr(self.instance, "external_id", ""))
        if bool(source) != bool(external_id):
            raise serializers.ValidationError({"external_id": "Source and external ID must be supplied together."})
        return attrs


class ApplicationSerializer(StrictModelSerializer):
    company_name = serializers.CharField(source="job.company.name", read_only=True)
    job_title = serializers.CharField(source="job.title", read_only=True)

    class Meta:
        model = Application
        fields = ("id", "campaign", "job", "company_name", "job_title", "status", "submitted_at", "in_progress_at", "failed_at", "failure_reason", "interview_scheduled_at", "notes", "source_reference", "created_at", "updated_at")
        read_only_fields = ("id", "status", "submitted_at", "in_progress_at", "failed_at", "failure_reason", "created_at", "updated_at")
        validators = []

    def to_representation(self, obj):
        data = super().to_representation(obj)
        request = self.context.get("request")
        if request and request.user.role == "CLIENT":
            data.pop("notes", None)
            data.pop("source_reference", None)
            data.pop("failure_reason", None)
        return data

    def validate_interview_scheduled_at(self, value):
        if value is not None and value <= timezone.now():
            raise serializers.ValidationError("Schedule interviews in the future.")
        return value


class ContactSerializer(StrictModelSerializer):
    company_name = serializers.CharField(source="company.name", read_only=True)

    class Meta:
        model = Contact
        fields = ("id", "company", "company_name", "name", "title", "email", "profile_url", "source")
        read_only_fields = ("id",)

    def validate_email(self, value):
        return value.strip().lower()


class OutreachSerializer(StrictModelSerializer):
    company_name = serializers.CharField(source="contact.company.name", read_only=True)
    contact_name = serializers.CharField(source="contact.name", read_only=True)

    class Meta:
        model = Outreach
        fields = ("id", "campaign", "contact", "company_name", "contact_name", "channel", "status", "subject", "body", "sent_at", "delivered_at", "bounced_at", "reply_at", "follow_up_due_at", "thread_reference", "notes")
        read_only_fields = ("id", "status", "sent_at", "delivered_at", "bounced_at", "reply_at")
        validators = []

    def to_representation(self, obj):
        data = super().to_representation(obj)
        request = self.context.get("request")
        if request and request.user.role == "CLIENT":
            for key in ("notes", "thread_reference", "subject", "body", "contact"):
                data.pop(key, None)
        return data


class SuppressionSerializer(StrictModelSerializer):
    class Meta:
        model = Suppression
        fields = ("id", "email", "reason", "created_at")
        read_only_fields = ("id", "created_at")
        extra_kwargs = {"email": {"validators": []}}

    def validate_email(self, value):
        return value.strip().lower()


class TemplateSerializer(StrictModelSerializer):
    class Meta:
        model = OutreachTemplate
        fields = ("id", "name", "subject", "body")
        read_only_fields = ("id",)
        extra_kwargs = {"name": {"validators": []}}


class TaskSerializer(StrictModelSerializer):
    assigned_to = serializers.IntegerField(source="assigned_to_id", required=False, allow_null=True, min_value=1)

    class Meta:
        model = HumanTask
        fields = ("id", "campaign", "task_type", "priority", "status", "assigned_to", "payload_json", "created_at", "completed_at")
        read_only_fields = ("id", "status", "created_at", "completed_at")
        extra_kwargs = {"priority": {"min_value": 1, "max_value": 5}}

    def validate_payload_json(self, value):
        if not isinstance(value, dict):
            raise serializers.ValidationError("Expected an object.")
        return value


class EventSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = ("id", "event_type", "summary", "created_at", "campaign")


class AuditSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = ("id", "event_type", "summary", "created_at", "campaign", "actor", "payload", "client_visible")


class TransitionSerializer(serializers.Serializer):
    status = serializers.CharField(max_length=24)
    notes = serializers.CharField(max_length=10000, required=False, allow_blank=True)
    interview_scheduled_at = serializers.DateTimeField(required=False, allow_null=True)

    def validate_interview_scheduled_at(self, value):
        if value is not None and value <= timezone.now():
            raise serializers.ValidationError("Schedule interviews in the future.")
        return value

    def validate(self, attrs):
        unknown = set(self.initial_data) - set(self.fields)
        if unknown:
            raise serializers.ValidationError({key: "This field is not writable." for key in unknown})
        return attrs


class CompletionSerializer(serializers.Serializer):
    notes = serializers.CharField(max_length=10000, required=False, allow_blank=True)

    def validate(self, attrs):
        unknown = set(self.initial_data) - set(self.fields)
        if unknown:
            raise serializers.ValidationError({key: "This field is not writable." for key in unknown})
        return attrs


class OperatorCandidateSerializer(CandidateProfileSerializer):
    user_id = serializers.IntegerField(read_only=True)
    email = serializers.EmailField(source="user.email", read_only=True)
    applications_submitted = serializers.IntegerField(read_only=True)
    review_status = serializers.ChoiceField(choices=("APPROVED", "CHANGES_REQUESTED"), required=False)

    class Meta(CandidateProfileSerializer.Meta):
        model = CandidateProfile
        fields = (*CandidateProfileSerializer.Meta.fields, "user_id", "email", "review_notes", "reviewed_at", "applications_submitted")
        read_only_fields = ("id", "created_at", "updated_at", "basics_complete", "user_id", "email", "reviewed_at")

    def validate(self, attrs):
        # Operators may review without a version token; editable facts still use
        # a version precondition to avoid silently overwriting candidate edits.
        facts = set(attrs) - {"review_status", "review_notes", "profile_version"}
        if facts and "profile_version" not in attrs:
            raise serializers.ValidationError({"profile_version": "Required when editing candidate facts."})
        original = self.initial_data
        if "profile_version" not in original:
            self.initial_data = {**original, "profile_version": self.instance.profile_version}
        try:
            attrs = super().validate(attrs)
        finally:
            self.initial_data = original
        if attrs.get("review_status") == "CHANGES_REQUESTED" and not attrs.get("review_notes", "").strip():
            raise serializers.ValidationError({"review_notes": "Explain the required changes."})
        return attrs
