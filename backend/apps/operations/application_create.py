"""Atomic manual application intake; never submits externally."""
from django.db import transaction
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.views import APIView
from apps.users.permissions import IsOperatorOrAdmin
from apps.campaigns.models import Campaign
from apps.jobs.models import Job
from apps.companies.models import Company
from .common import Conflict, visible_campaign
from .serializers import ApplicationSerializer, CompanySerializer, JobSerializer
from .services import ensure_workable, prepare, write_record


class ApplicationCreateSerializer(serializers.Serializer):
    campaign = serializers.UUIDField()
    job = serializers.UUIDField(required=False)
    new_job = serializers.DictField(required=False)
    notes = serializers.CharField(required=False, allow_blank=True, default="")
    source_reference = serializers.CharField(required=False, allow_blank=True, default="")

    def to_internal_value(self, data):
        unknown = set(data) - set(self.fields)
        if unknown:
            raise serializers.ValidationError({key: "This field is not writable." for key in unknown})
        return super().to_internal_value(data)

    def validate(self, attrs):
        if ("job" in attrs) == ("new_job" in attrs):
            raise serializers.ValidationError("Choose an existing job or enter a new job, exclusively.")
        return attrs


@transaction.atomic
def create_application(*, user, data):
    campaign = visible_campaign(user, data["campaign"])
    campaign = Campaign.objects.select_for_update().get(pk=campaign.pk)
    visible_campaign(user, campaign.pk)
    ensure_workable(campaign)
    if "new_job" in data:
        draft = dict(data["new_job"])
        unknown = set(draft) - {"company_name", "title", "location", "canonical_url"}
        if unknown:
            raise serializers.ValidationError({key: "This field is not writable." for key in unknown})
        company_serializer = CompanySerializer(data={"name": draft.pop("company_name", "")})
        company_serializer.is_valid(raise_exception=True)
        name = company_serializer.validated_data["name"]
        matches = Company.objects.filter(name__iexact=name)
        if matches.count() > 1:
            raise Conflict("Multiple companies have this name. Choose an existing job instead.")
        company = matches.first()
        if company is None:
            company = write_record(user=user, kind="companies", data=company_serializer.validated_data)
        job_serializer = JobSerializer(data={**draft, "company": str(company.pk)})
        job_serializer.is_valid(raise_exception=True)
        values = job_serializer.validated_data
        key = prepare("jobs", values)["identity_key"]
        job = Job.objects.filter(identity_key=key).first()
        if job and job.company_id != company.pk:
            raise Conflict("This job URL already belongs to a different company.")
        if job is None:
            job = write_record(user=user, kind="jobs", data=values)
    else:
        job = data["job"]
    serializer = ApplicationSerializer(data={"campaign": str(campaign.pk), "job": str(getattr(job, "pk", job)), "notes": data["notes"], "source_reference": data["source_reference"]})
    serializer.is_valid(raise_exception=True)
    return write_record(user=user, kind="applications", data=serializer.validated_data)


class ApplicationCreateView(APIView):
    permission_classes = (IsOperatorOrAdmin,)

    def post(self, request):
        serializer = ApplicationCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        application = create_application(user=request.user, data=serializer.validated_data)
        return Response(ApplicationSerializer(application, context={"request": request}).data, status=201)
