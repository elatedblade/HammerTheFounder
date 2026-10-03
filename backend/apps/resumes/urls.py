from django.urls import path

from .views import CandidateResumeCompleteView, CandidateResumeView, ResumeDownloadView, ResumeParseView, AdminCandidateResumesView, ResumeParsedTextView

app_name = "resumes"

urlpatterns = [
    path("resumes/<uuid:resume_id>/parsed-text/", ResumeParsedTextView.as_view()),
    path("admin/candidates/<int:candidate_id>/resumes/", AdminCandidateResumesView.as_view()),
    path("resumes/<uuid:resume_id>/download/", ResumeDownloadView.as_view()),
    path("resumes/<uuid:resume_id>/parse/", ResumeParseView.as_view()),
    path("candidate/resumes/", CandidateResumeView.as_view(), name="candidate-resumes"),
    path(
        "candidate/resumes/<uuid:resume_id>/complete/",
        CandidateResumeCompleteView.as_view(),
        name="candidate-resume-complete",
    ),
]
