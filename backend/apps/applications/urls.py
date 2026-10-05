from django.urls import path

from .views import (
    ApplicationDetailView,
    ApplicationListView,
    ApplicationTransitionView,
    CampaignApplicationListView,
)

app_name = "applications"

urlpatterns = [
    path("applications/", ApplicationListView.as_view(), name="list"),
    path(
        "applications/<uuid:application_id>/",
        ApplicationDetailView.as_view(),
        name="detail",
    ),
    path(
        "applications/<uuid:application_id>/transition/",
        ApplicationTransitionView.as_view(),
        name="transition",
    ),
    path(
        "campaigns/<uuid:campaign_id>/applications/",
        CampaignApplicationListView.as_view(),
        name="campaign-list",
    ),
]
