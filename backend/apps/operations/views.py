from django.http import Http404
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.models import Count, Q
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView
from apps.users.permissions import IsHTFUser, IsOperatorOrAdmin
from apps.users.models import User
from apps.candidates.selectors import get_operational_candidates
from apps.candidates.review import review_candidate
from apps.dashboard.selectors import campaign_metrics
from apps.dashboard.selectors import submitted_application_q
from apps.campaigns.selectors import get_visible_campaigns
from .common import bounded
from .selectors import records
from .services import write_record, transition_record, task_action
from .serializers import (
    CompanySerializer, JobSerializer, ApplicationSerializer, ContactSerializer,
    OutreachSerializer, SuppressionSerializer, TemplateSerializer, TaskSerializer,
    EventSerializer, AuditSerializer, TransitionSerializer, CompletionSerializer,
    OperatorCandidateSerializer,
)

SERIALIZERS = {"companies": CompanySerializer, "jobs": JobSerializer, "applications": ApplicationSerializer, "contacts": ContactSerializer, "outreach": OutreachSerializer, "suppression": SuppressionSerializer, "templates": TemplateSerializer, "tasks": TaskSerializer, "events": EventSerializer, "audit": AuditSerializer}


class ResourceView(APIView):
    kind = None
    read_only = False
    permission_classes = (IsHTFUser,)

    def get_permissions(self):
        permission = IsHTFUser if self.request.method == "GET" and self.kind in {"applications", "outreach", "events"} else IsOperatorOrAdmin
        return (permission(),)

    def get(self, request, object_id=None, campaign_id=None):
        try:
            queryset = records(request.user, self.kind, request.query_params, campaign_id)
            if object_id:
                obj = queryset.filter(pk=object_id).first()
                if obj is None:
                    raise Http404
                data = SERIALIZERS[self.kind](obj, context={"request": request}).data
            else:
                data = SERIALIZERS[self.kind](bounded(queryset, request.query_params), many=True, context={"request": request}).data
        except DjangoValidationError:
            raise ValidationError("Invalid filter identifier.")
        response = Response(data)
        response["Cache-Control"] = "no-store"
        return response

    def post(self, request, object_id=None, campaign_id=None):
        if self.read_only or object_id or campaign_id:
            from rest_framework.exceptions import MethodNotAllowed
            raise MethodNotAllowed("POST")
        serializer = SERIALIZERS[self.kind](data=request.data)
        serializer.is_valid(raise_exception=True)
        obj = write_record(user=request.user, kind=self.kind, data=serializer.validated_data)
        return Response(SERIALIZERS[self.kind](obj, context={"request": request}).data, status=201)

    def patch(self, request, object_id=None, campaign_id=None):
        if self.read_only or object_id is None or campaign_id:
            from rest_framework.exceptions import MethodNotAllowed
            raise MethodNotAllowed("PATCH")
        obj = records(request.user, self.kind).filter(pk=object_id).first()
        if obj is None:
            raise Http404
        serializer = SERIALIZERS[self.kind](instance=obj, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        obj = write_record(user=request.user, kind=self.kind, data=serializer.validated_data, object_id=object_id)
        return Response(SERIALIZERS[self.kind](obj, context={"request": request}).data)


class TransitionView(APIView):
    permission_classes = (IsOperatorOrAdmin,)
    kind = None

    def post(self, request, object_id):
        serializer = TransitionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        obj = transition_record(user=request.user, kind=self.kind, object_id=object_id, **serializer.validated_data)
        return Response(SERIALIZERS[self.kind](obj, context={"request": request}).data)


class TaskActionView(APIView):
    permission_classes = (IsOperatorOrAdmin,)
    action = None

    def post(self, request, object_id):
        serializer = CompletionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        obj = task_action(user=request.user, object_id=object_id, action=self.action, **serializer.validated_data)
        return Response(TaskSerializer(obj).data)


class MetricsView(APIView):
    permission_classes = (IsHTFUser,)

    def get(self, request, campaign_id=None):
        return Response(campaign_metrics(request.user, campaign_id or request.query_params.get("campaign")))


class OperatorListView(APIView):
    permission_classes = (IsOperatorOrAdmin,)

    def get(self, request):
        users = User.objects.filter(is_active=True, role__in=("OPERATOR", "ADMIN", "SUPERADMIN")).order_by("email")
        return Response(list(bounded(users, request.query_params).values("id", "email", "role")))


class CandidateReviewView(APIView):
    permission_classes = (IsOperatorOrAdmin,)

    def get(self, request, candidate_id=None):
        visible_campaigns = get_visible_campaigns(request.user)
        queryset = get_operational_candidates(request.user).annotate(
            applications_submitted=Count(
                "applications",
                filter=submitted_application_q("applications__") & Q(
                    applications__campaign__in=visible_campaigns
                ),
                distinct=True,
            )
        ).order_by("full_name", "id")
        if candidate_id:
            profile = queryset.filter(pk=candidate_id).first()
            if profile is None:
                raise Http404
            return Response(OperatorCandidateSerializer(profile).data)
        q = request.query_params.get("q", "").strip()[:200]
        if q:
            queryset = queryset.filter(Q(full_name__icontains=q) | Q(user__email__icontains=q))
        return Response(OperatorCandidateSerializer(bounded(queryset, request.query_params), many=True).data)

    def patch(self, request, candidate_id=None):
        if candidate_id is None:
            from rest_framework.exceptions import MethodNotAllowed
            raise MethodNotAllowed("PATCH")
        profile = get_operational_candidates(request.user).filter(pk=candidate_id).first()
        if profile is None:
            raise Http404
        serializer = OperatorCandidateSerializer(instance=profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        profile = review_candidate(actor=request.user, candidate_id=candidate_id, data=serializer.validated_data)
        return Response(OperatorCandidateSerializer(profile).data)
