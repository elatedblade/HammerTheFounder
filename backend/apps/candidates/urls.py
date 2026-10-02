from django.urls import path

from .views import CandidateProfileView

app_name = "candidates"

urlpatterns = [
    path("candidate/profile/", CandidateProfileView.as_view(), name="profile"),
]
