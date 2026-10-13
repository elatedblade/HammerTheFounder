from rest_framework.response import Response
from rest_framework.views import APIView

from .models import User
from .permissions import IsHTFUser, IsSuperAdmin
from .serializers import CurrentUserSerializer, ManagedUserSerializer, RoleChangeSerializer
from .services import change_user_role


class CurrentUserView(APIView):
    """Return the server-side identity and role for the current session."""

    permission_classes = (IsHTFUser,)

    def get(self, request):
        return Response(CurrentUserSerializer(request.user).data)


class ManagedUserListView(APIView):
    """List active Clerk identities for the superadmin console."""

    permission_classes = (IsSuperAdmin,)

    def get(self, request):
        users = User.objects.filter(
            is_active=True,
            identity_provider="clerk",
        ).order_by("email", "pk")
        return Response(ManagedUserSerializer(users, many=True).data)


class ManagedUserRoleView(APIView):
    """Change one local user's role from the superadmin console."""

    permission_classes = (IsSuperAdmin,)

    def patch(self, request, user_id):
        serializer = RoleChangeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = change_user_role(
            actor=request.user,
            user_id=user_id,
            role=serializer.validated_data["role"],
        )
        return Response(ManagedUserSerializer(user).data)
