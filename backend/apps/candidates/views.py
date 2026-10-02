from django.http import JsonResponse
from rest_framework.response import Response
from rest_framework.views import APIView

from .policies import IsActiveClient
from .selectors import get_own_profile
from .serializers import CandidateProfileSerializer
from .services import upsert_own_profile


class CandidateProfileView(APIView):
    permission_classes = (IsActiveClient,)

    def get(self, request):
        profile = get_own_profile(request.user)
        if profile is None:
            return JsonResponse(None, safe=False)
        return Response(CandidateProfileSerializer(profile).data)

    def patch(self, request):
        serializer = CandidateProfileSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        profile = upsert_own_profile(
            user=request.user,
            data=serializer.validated_data,
        )
        return Response(CandidateProfileSerializer(profile).data)
