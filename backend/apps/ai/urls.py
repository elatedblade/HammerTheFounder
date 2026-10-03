from django.urls import path
from .views import RunsView, RunDetailView

urlpatterns = [path("ai/runs/", RunsView.as_view()), path("ai/runs/<uuid:pk>/", RunDetailView.as_view())]
