from rest_framework.response import Response
from rest_framework.views import APIView

from .permissions import IsHTFUser
from .serializers import CurrentUserSerializer


class CurrentUserView(APIView):
    """Return the server-side identity and role for the current session."""

    permission_classes = (IsHTFUser,)

    def get(self, request):
        return Response(CurrentUserSerializer(request.user).data)
