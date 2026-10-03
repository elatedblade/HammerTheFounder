from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView
from apps.users.permissions import IsOperatorOrAdmin
from apps.campaigns.selectors import get_visible_campaigns
from apps.billing.services import filter_campaign
from .models import AIRun
from .serializers import AIRunSerializer, AIRunCreateSerializer
from .services import create_run


class RunsView(APIView):
    permission_classes = (IsOperatorOrAdmin,)

    def get(self, request):
        rows = AIRun.objects.filter(campaign__in=get_visible_campaigns(request.user))
        rows = filter_campaign(rows, request)
        return Response(AIRunSerializer(rows[:200], many=True).data)

    def post(self, request):
        serializer = AIRunCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        run = create_run(user=request.user, data=serializer.validated_data)
        run.refresh_from_db()
        return Response(AIRunSerializer(run).data, status=201)


class RunDetailView(APIView):
    permission_classes = (IsOperatorOrAdmin,)

    def get(self, request, pk):
        run = get_object_or_404(AIRun, pk=pk, campaign__in=get_visible_campaigns(request.user))
        return Response(AIRunSerializer(run).data)
