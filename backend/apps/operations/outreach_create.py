"""Atomic intake for manually reviewed outreach drafts."""
from django.db import transaction
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.views import APIView
from apps.campaigns.models import Campaign
from apps.companies.models import Company
from apps.contacts.models import Contact
from apps.users.permissions import IsOperatorOrAdmin
from .common import visible_campaign
from .serializers import StrictModelSerializer, CompanySerializer, OutreachSerializer
from .services import ensure_workable, prepare, write_record


class NewContactSerializer(StrictModelSerializer):
    class Meta:
        model = Contact
        fields = ("name", "title", "email", "profile_url", "source")


class OutreachCreateSerializer(serializers.Serializer):
    campaign = serializers.UUIDField()
    contact = serializers.PrimaryKeyRelatedField(queryset=Contact.objects.all(), required=False)
    contact_data = NewContactSerializer(required=False)
    company = serializers.PrimaryKeyRelatedField(queryset=Company.objects.all(), required=False)
    company_data = CompanySerializer(required=False)
    channel = serializers.ChoiceField(choices=("EMAIL", "LINKEDIN", "WHATSAPP"))
    subject = serializers.CharField(max_length=500, required=False, allow_blank=True)
    body = serializers.CharField(max_length=20000)
    notes = serializers.CharField(max_length=10000, required=False, allow_blank=True)

    def to_internal_value(self, data):
        unknown = set(data) - set(self.fields)
        if unknown:
            raise serializers.ValidationError({key: "This field is not writable." for key in unknown})
        return super().to_internal_value(data)

    def validate(self, attrs):
        if ("contact" in attrs) == ("contact_data" in attrs):
            raise serializers.ValidationError({"contact": "Choose an existing contact or enter contact data."})
        if "contact" in attrs:
            if {"company", "company_data"} & attrs.keys():
                raise serializers.ValidationError({"company": "Existing contacts already have a company."})
        elif ("company" in attrs) == ("company_data" in attrs):
            raise serializers.ValidationError({"company": "Choose a company or enter company data."})
        return attrs


@transaction.atomic
def create_outreach(*, user, data):
    values = dict(data)
    campaign = visible_campaign(user, values.pop("campaign"))
    campaign = Campaign.objects.select_for_update().get(pk=campaign.pk)
    visible_campaign(user, campaign.pk)
    ensure_workable(campaign)
    contact_data = values.pop("contact_data", None)
    if contact_data is not None:
        company = values.pop("company", None)
        company_data = values.pop("company_data", None)
        if company is None:
            prepared = prepare("companies", company_data)
            company = Company.objects.filter(identity_key=prepared["identity_key"]).first()
            if company is None:
                company = write_record(user=user, kind="companies", data=company_data)
        contact_data = {**contact_data, "company": company}
        prepared = prepare("contacts", contact_data)
        contact = Contact.objects.filter(identity_key=prepared["identity_key"]).first()
        if contact is None:
            contact = write_record(user=user, kind="contacts", data=contact_data)
        values["contact"] = contact
    return write_record(user=user, kind="outreach", data={**values, "campaign": campaign})


class OutreachCreateView(APIView):
    permission_classes = (IsOperatorOrAdmin,)

    def post(self, request):
        serializer = OutreachCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        outreach = create_outreach(user=request.user, data=serializer.validated_data)
        return Response(OutreachSerializer(outreach, context={"request": request}).data, status=201)
