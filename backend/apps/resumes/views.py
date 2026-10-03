from datetime import timedelta

from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.candidates.policies import IsActiveClient

from .selectors import get_own_resumes
from .serializers import ResumeSerializer, ResumeUploadRequestSerializer, OperationalParsedTextSerializer
from .services import authorize_own_resume_upload, complete_own_resume_upload
from apps.users.permissions import IsHTFUser, IsOperatorOrAdmin
from .processing import download_resume, queue_parse, visible_resumes


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


class CandidateResumeCompleteView(APIView):
    permission_classes = (IsActiveClient,)

    def post(self, request, resume_id):
        resume = complete_own_resume_upload(user=request.user, resume_id=resume_id)
        response = Response(ResumeSerializer(resume).data)
        response["Cache-Control"] = "no-store"
        return response


class ResumeDownloadView(APIView):
    permission_classes = (IsHTFUser,)

    def post(self, request, resume_id):
        response = Response(download_resume(user=request.user, pk=resume_id))
        response["Cache-Control"] = "no-store"
        return response


class ResumeParseView(APIView):
    permission_classes = (IsOperatorOrAdmin,)

    def post(self, request, resume_id):
        item = queue_parse(user=request.user, pk=resume_id)
        item.refresh_from_db()
        return Response(ResumeSerializer(item).data)


class AdminCandidateResumesView(APIView):
    permission_classes = (IsOperatorOrAdmin,)

    def get(self, request, candidate_id):
        from apps.candidates.selectors import get_operational_candidates
        from django.shortcuts import get_object_or_404
        get_object_or_404(get_operational_candidates(request.user), pk=candidate_id)
        rows = visible_resumes(request.user).filter(candidate_id=candidate_id)[:200]
        response = Response(ResumeSerializer(rows, many=True).data)
        response["Cache-Control"] = "no-store"
        return response


class ResumeParsedTextView(APIView):
    permission_classes = (IsOperatorOrAdmin,)

    def get(self, request, resume_id):
        from .processing import get_resume
        from apps.billing.services import Conflict
        item = get_resume(request.user, resume_id)
        if item.parse_status != "PARSED":
            raise Conflict("Resume text is not available until parsing completes successfully.")
        response = Response(OperationalParsedTextSerializer(item).data)
        response["Cache-Control"] = "no-store"
        return response
