from django.urls import path

from .views import CandidateResumeView

app_name = "resumes"

urlpatterns = [
    path("candidate/resumes/", CandidateResumeView.as_view(), name="candidate-resumes"),
]
