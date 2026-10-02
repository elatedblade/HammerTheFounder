from django.urls import path

from .views import CandidateResumeCompleteView, CandidateResumeView

app_name = "resumes"

urlpatterns = [
    path("candidate/resumes/", CandidateResumeView.as_view(), name="candidate-resumes"),
    path(
        "candidate/resumes/<uuid:resume_id>/complete/",
        CandidateResumeCompleteView.as_view(),
        name="candidate-resume-complete",
    ),
]
