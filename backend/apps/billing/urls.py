from django.urls import path
from .views import PaymentsView, PaymentActionView, InstructionsView

urlpatterns = [
    path("billing/payments/", PaymentsView.as_view()),
    path("billing/payments/<uuid:pk>/verify/", PaymentActionView.as_view(verify=True)),
    path("billing/payments/<uuid:pk>/transition/", PaymentActionView.as_view()),
    path("billing/instructions/", InstructionsView.as_view()),
]
