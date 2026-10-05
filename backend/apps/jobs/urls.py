from django.urls import path

from .views import JobDetailView, JobListView

app_name = "jobs"

urlpatterns = [
    path("jobs/", JobListView.as_view(), name="list"),
    path("jobs/<uuid:job_id>/", JobDetailView.as_view(), name="detail"),
]
