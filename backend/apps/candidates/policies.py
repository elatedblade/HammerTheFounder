from rest_framework.permissions import BasePermission

from apps.users.models import User


class IsActiveClient(BasePermission):
    """Allow only active CLIENT identities on candidate self-service APIs."""

    message = "An active client role is required."

    def has_permission(self, request, view):
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and user.is_active
            and user.role == User.Role.CLIENT
        )
