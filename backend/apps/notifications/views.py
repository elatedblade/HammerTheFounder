from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView
from apps.users.permissions import IsHTFUser, IsOperatorOrAdmin
from apps.campaigns.selectors import get_visible_campaigns
from apps.billing.services import filter_campaign
from .models import Notification, NotificationTemplate
from .serializers import NotificationSerializer, NotificationCreateSerializer, TemplateSerializer
from .services import create_notification, dispatch_notification
from apps.operations.common import bounded


class NotificationsView(APIView):
    permission_classes = (IsHTFUser,)

    def get(self, request):
        items = Notification.objects.filter(campaign__in=get_visible_campaigns(request.user))
        items = filter_campaign(items, request)
        if request.user.role == "CLIENT":
            items = items.filter(status="SENT")
        params = {"limit": "200", **request.query_params.dict()}
        response = Response(NotificationSerializer(bounded(items.order_by("-created_at", "-id"), params), many=True).data)
        response["Cache-Control"] = "no-store"
        return response

    def post(self, request):
        serializer = NotificationCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        item = create_notification(user=request.user, data=serializer.validated_data)
        return Response(NotificationSerializer(item).data, status=201)


class NotificationActionView(APIView):
    permission_classes = (IsOperatorOrAdmin,)
    manual = False

    def post(self, request, pk):
        get_object_or_404(Notification, pk=pk, campaign__in=get_visible_campaigns(request.user))
        item = dispatch_notification(user=request.user, notification_id=pk, manual=self.manual)
        item.refresh_from_db()
        return Response(NotificationSerializer(item).data)


class TemplatesView(APIView):
    permission_classes = (IsOperatorOrAdmin,)

    def get(self, request):
        return Response(TemplateSerializer(NotificationTemplate.objects.order_by("name")[:200], many=True).data)

    def post(self, request):
        serializer = TemplateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=201)
