from django.urls import path

from .views import CompanyDetailView, CompanyListView

app_name = "companies"

urlpatterns = [
    path("companies/", CompanyListView.as_view(), name="list"),
    path("companies/<uuid:company_id>/", CompanyDetailView.as_view(), name="detail"),
]
