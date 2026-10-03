from django.urls import path

from .views import (
    CampaignDetailView,
    CampaignListView,
    CampaignPauseView,
    CampaignResumeView,
    CampaignStartView,
    CampaignCompleteView, CampaignCancelView,
)

app_name = "campaigns"

urlpatterns = [
    path("campaigns/<uuid:campaign_id>/complete/", CampaignCompleteView.as_view(), name="complete"),
    path("campaigns/<uuid:campaign_id>/cancel/", CampaignCancelView.as_view(), name="cancel"),
    path("campaigns/", CampaignListView.as_view(), name="list"),
    path("campaigns/<uuid:campaign_id>/", CampaignDetailView.as_view(), name="detail"),
    path(
        "campaigns/<uuid:campaign_id>/start/",
        CampaignStartView.as_view(),
        name="start",
    ),
    path(
        "campaigns/<uuid:campaign_id>/pause/",
        CampaignPauseView.as_view(),
        name="pause",
    ),
    path(
        "campaigns/<uuid:campaign_id>/resume/",
        CampaignResumeView.as_view(),
        name="resume",
    ),
]
