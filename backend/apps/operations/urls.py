from django.urls import path
from .views import ResourceView, TransitionView, TaskActionView, MetricsView, CandidateReviewView, OperatorListView

app_name = "operations"
urlpatterns = [
    path("admin/candidates/", CandidateReviewView.as_view(), name="candidates"),
    path("admin/candidates/<int:candidate_id>/", CandidateReviewView.as_view(), name="candidate-detail"),
    path("admin/operators/", OperatorListView.as_view(), name="operators"),
    path("dashboard/", MetricsView.as_view(), name="dashboard"),
    path("campaigns/<uuid:campaign_id>/metrics/", MetricsView.as_view(), name="campaign-metrics"),
    path("admin/tasks/<uuid:object_id>/claim/", TaskActionView.as_view(action="claim"), name="task-claim"),
    path("admin/tasks/<uuid:object_id>/complete/", TaskActionView.as_view(action="complete"), name="task-complete"),
]

for kind, route in (("companies", "companies"), ("jobs", "jobs"), ("applications", "applications"), ("contacts", "contacts"), ("outreach", "outreach"), ("suppression", "suppression"), ("templates", "outreach/templates"), ("tasks", "admin/tasks"), ("events", "events"), ("audit", "admin/audit")):
    read_only = kind in {"events", "audit"}
    urlpatterns.append(path(f"{route}/", ResourceView.as_view(kind=kind, read_only=read_only), name=f"{kind}-list"))
    if kind not in {"suppression", "templates", "events", "audit"}:
        urlpatterns.append(path(f"{route}/<uuid:object_id>/", ResourceView.as_view(kind=kind), name=f"{kind}-detail"))
    if kind in {"applications", "outreach"}:
        urlpatterns.append(path(f"{route}/<uuid:object_id>/transition/", TransitionView.as_view(kind=kind), name=f"{kind}-transition"))

for kind in ("applications", "outreach", "events"):
    urlpatterns.append(path(f"campaigns/<uuid:campaign_id>/{kind}/", ResourceView.as_view(kind=kind, read_only=True), name=f"campaign-{kind}"))
