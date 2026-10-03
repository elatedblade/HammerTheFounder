import os
from django.conf import settings
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import ValidationError
from apps.users.permissions import IsHTFUser, IsAdmin
from apps.campaigns.selectors import get_visible_campaigns
from apps.candidates.selectors import get_visible_candidate_ids
from .models import Payment
from .serializers import PaymentSerializer, PaymentCreateSerializer, VerifySerializer, TransitionSerializer
from .services import create_payment, transition_payment, filter_campaign


class PaymentsView(APIView):
    permission_classes = (IsHTFUser,)

    def get(self, request):
        rows = Payment.objects.filter(campaign__in=get_visible_campaigns(request.user))
        rows = filter_campaign(rows, request)
        candidate = request.query_params.get("candidate")
        if candidate is not None:
            try:
                candidate = int(candidate)
            except (TypeError, ValueError):
                raise ValidationError({"candidate": "Expected a positive integer."})
            if candidate < 1:
                raise ValidationError({"candidate": "Expected a positive integer."})
            rows = rows.filter(campaign__candidate_id=candidate, campaign__candidate_id__in=get_visible_candidate_ids(request.user))
        try:
            limit = min(max(int(request.query_params.get("limit", 200)), 1), 500)
            offset = max(int(request.query_params.get("offset", 0)), 0)
        except (ValueError, TypeError):
            raise ValidationError({"limit": "Use integer pagination values."})
        rows = rows.order_by("-created_at", "-id")[offset:offset + limit]
        response = Response(PaymentSerializer(rows, many=True, context={"request": request}).data)
        response["Cache-Control"] = "no-store"
        return response

    def post(self, request):
        serializer = PaymentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        key = request.headers.get("Idempotency-Key")
        if key and len(key) > 128:
            raise ValidationError({"idempotency_key": "Maximum length is 128."})
        payment, created = create_payment(user=request.user, data=serializer.validated_data, key=key)
        return Response(PaymentSerializer(payment, context={"request": request}).data, status=201 if created else 200)


class PaymentActionView(APIView):
    permission_classes = (IsAdmin,)
    verify = False

    def post(self, request, pk):
        get_object_or_404(Payment, pk=pk)
        serializer = (VerifySerializer if self.verify else TransitionSerializer)(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = dict(serializer.validated_data)
        target = "VERIFIED" if self.verify else data.pop("status")
        payment = transition_payment(user=request.user, payment_id=pk, target=target, **data)
        return Response(PaymentSerializer(payment, context={"request": request}).data)


class InstructionsView(APIView):
    permission_classes = (IsHTFUser,)

    def get(self, request):
        values = {key: getattr(settings, "UPI_" + key.upper(), os.getenv("UPI_" + key.upper(), "")) for key in ("id", "payee_name", "instructions")}
        configured = bool(values["id"] and values["payee_name"])
        return Response({"configured": configured, "upi_id": values["id"] if configured else "", "payee_name": values["payee_name"] if configured else "", "instructions": values["instructions"]})
