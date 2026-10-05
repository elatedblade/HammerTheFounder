from django.http import Http404
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.permissions import IsOperatorOrAdmin

from .selectors import get_visible_companies, get_visible_company
from .serializers import CompanySerializer


class CompanyListView(APIView):
    permission_classes = (IsOperatorOrAdmin,)

    def get(self, request):
        companies = get_visible_companies(request.user)
        return Response(CompanySerializer(companies, many=True).data)

    def post(self, request):
        serializer = CompanySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        company = serializer.save()
        return Response(CompanySerializer(company).data, status=201)


class CompanyDetailView(APIView):
    permission_classes = (IsOperatorOrAdmin,)

    def get_object(self, request, company_id):
        company = get_visible_company(request.user, company_id)
        if company is None:
            raise Http404
        return company

    def get(self, request, company_id):
        return Response(CompanySerializer(self.get_object(request, company_id)).data)

    def patch(self, request, company_id):
        company = self.get_object(request, company_id)
        serializer = CompanySerializer(company, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(CompanySerializer(company).data)
