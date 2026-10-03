from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import ValidationError
from apps.candidates.policies import IsActiveClient
from apps.users.permissions import IsOperatorOrAdmin
from apps.operations.common import bounded, administrator
from .models import Inquiry
from .serializers import InquirySerializer, InquiryAdminSerializer, InquiryCreateSerializer, InquiryUpdateSerializer
from .services import create_inquiry, update_inquiry, convert_inquiry, whatsapp_configured
from .selectors import operational_inquiries


class PublicContactView(APIView):
    permission_classes = ()
    authentication_classes = ()
    def get(self, request): return Response({"whatsapp_configured": whatsapp_configured()})


class CandidateInquiryView(APIView):
    permission_classes = (IsActiveClient,)
    def get(self, request): return Response(InquirySerializer(bounded(Inquiry.objects.filter(user=request.user), request.query_params), many=True).data)
    def post(self, request):
        serializer = InquiryCreateSerializer(data=request.data); serializer.is_valid(raise_exception=True)
        return Response(InquirySerializer(create_inquiry(user=request.user, **serializer.validated_data)).data, status=201)


class AdminInquiryListView(APIView):
    permission_classes = (IsOperatorOrAdmin,)
    def get(self, request):
        queryset = operational_inquiries(request.user)
        if request.query_params.get("status"):
            status = request.query_params["status"]
            if status not in Inquiry.Status.values:
                raise ValidationError({"status": "Choose a valid inquiry status."})
            queryset = queryset.filter(status=status)
        return Response(InquiryAdminSerializer(bounded(queryset, request.query_params), many=True).data)


class AdminInquiryDetailView(APIView):
    permission_classes = (IsOperatorOrAdmin,)
    def get(self, request, inquiry_id):
        from django.shortcuts import get_object_or_404
        inquiry = get_object_or_404(operational_inquiries(request.user), pk=inquiry_id)
        return Response(InquiryAdminSerializer(inquiry).data)

    def patch(self, request, inquiry_id):
        serializer = InquiryUpdateSerializer(data=request.data); serializer.is_valid(raise_exception=True)
        return Response(InquiryAdminSerializer(update_inquiry(inquiry_id=inquiry_id, actor=request.user, data=serializer.validated_data)).data)


class AdminInquiryConvertView(APIView):
    permission_classes = (IsOperatorOrAdmin,)
    def post(self, request, inquiry_id):
        if request.data:
            raise ValidationError({"body": "Conversion does not accept a request body."})
        inquiry, campaign = convert_inquiry(inquiry_id=inquiry_id, actor=request.user)
        return Response({"inquiry": InquiryAdminSerializer(inquiry).data, "campaign_id": campaign.id})
