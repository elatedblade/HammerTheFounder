from django.urls import path
from .views import NotificationsView, NotificationActionView, TemplatesView

urlpatterns = [
    path("notifications/", NotificationsView.as_view()),
    path("notifications/templates/", TemplatesView.as_view()),
    path("notifications/<uuid:pk>/send/", NotificationActionView.as_view()),
    path("notifications/<uuid:pk>/mark-sent/", NotificationActionView.as_view(manual=True)),
]
