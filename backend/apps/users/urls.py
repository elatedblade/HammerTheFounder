from django.urls import path

from .views import CurrentUserView, ManagedUserListView, ManagedUserRoleView

app_name = "users"

urlpatterns = [
    path("me/", CurrentUserView.as_view(), name="me"),
    path("admin/users/", ManagedUserListView.as_view(), name="admin-users"),
    path(
        "admin/users/<int:user_id>/role/",
        ManagedUserRoleView.as_view(),
        name="admin-user-role",
    ),
]
