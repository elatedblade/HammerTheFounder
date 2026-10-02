from rest_framework.permissions import BasePermission

from .models import User


class IsHTFUser(BasePermission):
    """Require an active local identity before allowing API access."""

    message = "An active HTF identity is required."

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.is_active)


class IsOperatorOrAdmin(BasePermission):
    """Allow operational work to operators and administrators only."""

    message = "An operator or administrator role is required."

    def has_permission(self, request, view):
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and user.is_active
            and user.role
            in {User.Role.OPERATOR, User.Role.ADMIN, User.Role.SUPERADMIN}
        )


class IsAdmin(BasePermission):
    """Allow system administration to administrators only."""

    message = "An administrator role is required."

    def has_permission(self, request, view):
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and user.is_active
            and user.role in {User.Role.ADMIN, User.Role.SUPERADMIN}
        )
