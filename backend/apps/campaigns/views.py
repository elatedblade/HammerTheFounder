from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.permissions import IsHTFUser, IsOperatorOrAdmin

from .selectors import get_visible_campaign, get_visible_campaigns
from .serializers import CampaignCreateSerializer, CampaignSerializer, CampaignUpdateSerializer
from .services import (
    create_campaign,
    pause_campaign,
    resume_campaign,
    start_campaign,
    complete_campaign, cancel_campaign, update_campaign,
)


class CampaignListView(APIView):
    def get_permissions(self):
        permission_class = (
            IsOperatorOrAdmin if self.request.method == "POST" else IsHTFUser
        )
        return (permission_class(),)

    def get(self, request):
        response = Response(
            CampaignSerializer(get_visible_campaigns(request.user)[:500], many=True, context={"request": request}).data
        )
        response["Cache-Control"] = "no-store"
        return response

    def post(self, request):
        serializer = CampaignCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        campaign = create_campaign(**serializer.validated_data, actor=request.user)
        return Response(CampaignSerializer(campaign, context={"request": request}).data, status=201)


class CampaignDetailView(APIView):
    permission_classes = (IsHTFUser,)

    def get(self, request, campaign_id):
        campaign = get_visible_campaign(request.user, campaign_id)
        if campaign is None:
            from django.http import Http404

            raise Http404
        response = Response(CampaignSerializer(campaign, context={"request": request}).data)
        response["Cache-Control"] = "no-store"
        return response

    def patch(self, request, campaign_id):
        serializer = CampaignUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        campaign = update_campaign(campaign_id=campaign_id, actor=request.user, data=serializer.validated_data)
        return Response(CampaignSerializer(campaign, context={"request": request}).data)


class CampaignActionView(APIView):
    permission_classes = (IsOperatorOrAdmin,)
    action = None

    def post(self, request, campaign_id):
        campaign = self.action(campaign_id=campaign_id, actor=request.user)
        return Response(CampaignSerializer(campaign, context={"request": request}).data)


class CampaignStartView(CampaignActionView):
    action = staticmethod(start_campaign)


class CampaignPauseView(CampaignActionView):
    action = staticmethod(pause_campaign)


class CampaignResumeView(CampaignActionView):
    action = staticmethod(resume_campaign)


class CampaignCompleteView(CampaignActionView):
    action = staticmethod(complete_campaign)


class CampaignCancelView(CampaignActionView):
    action = staticmethod(cancel_campaign)
