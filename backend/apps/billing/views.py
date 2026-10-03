import os
from django.conf import settings
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import ValidationError
from apps.users.permissions import IsHTFUser, IsAdmin
from apps.campaigns.selectors import get_visible_campaigns
from .models import Payment
from .serializers import PaymentSerializer, PaymentCreateSerializer, VerifySerializer, TransitionSerializer
from .services import create_payment, transition_payment, filter_campaign


class PaymentsView(APIView):
    permission_classes = (IsHTFUser,)

    def get(self, request):
        rows = Payment.objects.filter(campaign__in=get_visible_campaigns(request.user))
        rows = filter_campaign(rows, request)
        return Response(PaymentSerializer(rows[:200], many=True, context={"request": request}).data)

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
