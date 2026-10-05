from django.http import Http404
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.permissions import IsHTFUser, IsOperatorOrAdmin

from .selectors import get_visible_application, get_visible_applications
from .serializers import (
    ApplicationCreateSerializer,
    ApplicationSerializer,
    ApplicationTransitionSerializer,
)
from .services import create_application, transition_application


class ApplicationListView(APIView):
    def get_permissions(self):
        return (IsOperatorOrAdmin() if self.request.method == "POST" else IsHTFUser(),)

    def get(self, request):
        applications = get_visible_applications(
            request.user, campaign_id=request.query_params.get("campaign_id")
        )
        response = Response(ApplicationSerializer(applications, many=True).data)
        response["Cache-Control"] = "no-store"
        return response

    def post(self, request):
        serializer = ApplicationCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        application = create_application(operator=request.user, **serializer.validated_data)
        return Response(ApplicationSerializer(application).data, status=201)


class CampaignApplicationListView(APIView):
    permission_classes = (IsHTFUser,)

    def get(self, request, campaign_id):
        applications = get_visible_applications(request.user, campaign_id=campaign_id)
        if not applications.exists():
            # Return an empty list for a visible campaign with no applications,
            # but do not disclose whether an inaccessible campaign exists.
            from apps.campaigns.selectors import get_visible_campaign

            if get_visible_campaign(request.user, campaign_id) is None:
                raise Http404
        response = Response(ApplicationSerializer(applications, many=True).data)
        response["Cache-Control"] = "no-store"
        return response


class ApplicationDetailView(APIView):
    permission_classes = (IsHTFUser,)

    def get_object(self, request, application_id):
        application = get_visible_application(request.user, application_id)
        if application is None:
            raise Http404
        return application

    def get(self, request, application_id):
        response = Response(ApplicationSerializer(self.get_object(request, application_id)).data)
        response["Cache-Control"] = "no-store"
        return response


class ApplicationTransitionView(APIView):
    permission_classes = (IsOperatorOrAdmin,)

    def post(self, request, application_id):
        serializer = ApplicationTransitionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        application = transition_application(
            application_id=application_id,
            operator=request.user,
            target_status=serializer.validated_data["status"],
            notes=serializer.validated_data.get("notes"),
        )
        return Response(ApplicationSerializer(application).data)
