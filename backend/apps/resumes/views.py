from datetime import timedelta

from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.candidates.policies import IsActiveClient

from .selectors import get_own_resumes
from .serializers import ResumeSerializer, ResumeUploadRequestSerializer
from .services import authorize_own_resume_upload


class CandidateResumeView(APIView):
    permission_classes = (IsActiveClient,)

    def get(self, request):
        response = Response(ResumeSerializer(get_own_resumes(request.user), many=True).data)
        response["Cache-Control"] = "no-store"
        return response

    def post(self, request):
        serializer = ResumeUploadRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        resume, upload = authorize_own_resume_upload(
            user=request.user, data=serializer.validated_data
        )
        response = Response(
            {
                "id": str(resume.id),
                "upload_url": upload.url,
                "upload_headers": upload.headers,
                "expires_at": (
                    timezone.now() + timedelta(seconds=upload.expires_in)
                ).isoformat(),
                "resume": ResumeSerializer(resume).data,
                "upload": {
                    "url": upload.url,
                    "method": "PUT",
                    "headers": upload.headers,
                    "expires_in": upload.expires_in,
                },
            },
            status=status.HTTP_201_CREATED,
        )
        response["Cache-Control"] = "no-store"
        return response
