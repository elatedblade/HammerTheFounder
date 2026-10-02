from django.urls import path

from .views import CurrentUserView

app_name = "users"

urlpatterns = [
    path("me/", CurrentUserView.as_view(), name="me"),
]
