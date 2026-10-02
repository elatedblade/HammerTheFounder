from django.db import IntegrityError
from django.http import Http404
from rest_framework.exceptions import APIException
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.permissions import IsOperatorOrAdmin

from .selectors import get_visible_job, get_visible_jobs
from .serializers import JobSerializer


class DuplicateJob(APIException):
    status_code = 409
    default_detail = "A job with this source and ID already exists."
    default_code = "job_duplicate"


class JobListView(APIView):
    permission_classes = (IsOperatorOrAdmin,)

    def get(self, request):
        jobs = get_visible_jobs(
            request.user,
            company_id=request.query_params.get("company_id"),
            status=request.query_params.get("status"),
            external_source=request.query_params.get("external_source"),
        )
        return Response(JobSerializer(jobs, many=True).data)

    def post(self, request):
        serializer = JobSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            job = serializer.save()
        except IntegrityError as exc:
            raise DuplicateJob() from exc
        return Response(JobSerializer(job).data, status=201)


class JobDetailView(APIView):
    permission_classes = (IsOperatorOrAdmin,)

    def get_object(self, request, job_id):
        job = get_visible_job(request.user, job_id)
        if job is None:
            raise Http404
        return job

    def get(self, request, job_id):
        return Response(JobSerializer(self.get_object(request, job_id)).data)

    def patch(self, request, job_id):
        job = self.get_object(request, job_id)
        serializer = JobSerializer(job, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        try:
            serializer.save()
        except IntegrityError as exc:
            raise DuplicateJob() from exc
        return Response(JobSerializer(job).data)
