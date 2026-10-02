import pytest
from django.urls import include, path, reverse
from django.test import override_settings
from rest_framework.test import APIClient

from apps.companies.models import Company
from apps.jobs.models import Job
from apps.users.models import User


pytestmark = pytest.mark.django_db

urlpatterns = [
    path("api/v1/", include("apps.companies.urls")),
    path("api/v1/", include("apps.jobs.urls")),
]


def make_user(subject="operator", role=User.Role.OPERATOR):
    return User.objects.create_user(
        "clerk", subject, email=f"{subject}@example.com", role=role
    )


def client_for(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


def company_payload(**overrides):
    payload = {
        "name": "Acme Corporation",
        "website": "https://acme.example.com",
        "industry": "Software",
        "location": "London",
        "metadata": {"source": "operator"},
    }
    payload.update(overrides)
    return payload


def job_payload(company, **overrides):
    payload = {
        "company_id": str(company.id),
        "external_source": "Greenhouse",
        "external_id": "job-123",
        "canonical_url": "https://jobs.example.com/job-123",
        "title": "Staff Engineer",
        "location": "London / Remote",
        "employment_type": "FULL_TIME",
        "description": "Build reliable systems.",
        "fingerprint": "acme-staff-engineer-london",
        "metadata": {"department": "Platform"},
    }
    payload.update(overrides)
    return payload


@override_settings(ROOT_URLCONF=__name__)
def test_only_operators_can_access_canonical_companies_and_jobs():
    operator = make_user("operator")
    client_user = make_user("client", role=User.Role.CLIENT)
    company = Company.objects.create(name="Acme Corporation")
    Job.objects.create(
        company=company,
        external_source="greenhouse",
        external_id="job-123",
        title="Staff Engineer",
    )

    forbidden_companies = client_for(client_user).get(reverse("companies:list"))
    forbidden_jobs = client_for(client_user).get(reverse("jobs:list"))
    visible_companies = client_for(operator).get(reverse("companies:list"))
    visible_jobs = client_for(operator).get(reverse("jobs:list"))

    assert forbidden_companies.status_code == 403
    assert forbidden_companies.json()["code"] == "FORBIDDEN"
    assert forbidden_jobs.status_code == 403
    assert visible_companies.status_code == 200
    assert visible_companies.json()[0]["name"] == "Acme Corporation"
    assert visible_jobs.status_code == 200
    assert visible_jobs.json()[0]["company_id"] == str(company.id)


@override_settings(ROOT_URLCONF=__name__)
def test_operator_can_create_company_and_normalized_job():
    operator_client = client_for(make_user("operator"))

    company_response = operator_client.post(
        reverse("companies:list"), company_payload(), format="json"
    )

    assert company_response.status_code == 201
    company = Company.objects.get(pk=company_response.json()["id"])
    assert company.normalized_name == "acme corporation"
    assert company_response.json()["metadata"] == {"source": "operator"}

    job_response = operator_client.post(
        reverse("jobs:list"), job_payload(company), format="json"
    )

    assert job_response.status_code == 201
    assert job_response.json()["external_source"] == "greenhouse"
    assert job_response.json()["metadata"] == {"department": "Platform"}
    assert job_response.json()["status"] == "ACTIVE"
    assert Job.objects.get(pk=job_response.json()["id"]).external_source == "greenhouse"


@override_settings(ROOT_URLCONF=__name__)
def test_job_external_source_and_id_are_deduplicated():
    operator_client = client_for(make_user("operator"))
    company = Company.objects.create(name="Acme Corporation")
    operator_client.post(reverse("jobs:list"), job_payload(company), format="json")

    duplicate = operator_client.post(
        reverse("jobs:list"), job_payload(company, external_source=" GREENHOUSE "), format="json"
    )

    assert duplicate.status_code == 400
    assert "external_id" in duplicate.json()["details"]
    assert Job.objects.count() == 1


@override_settings(ROOT_URLCONF=__name__)
def test_operator_can_patch_job_but_client_cannot_read_it():
    operator = make_user("operator")
    company = Company.objects.create(name="Acme Corporation")
    job = Job.objects.create(
        company=company,
        external_source="greenhouse",
        external_id="job-123",
        title="Staff Engineer",
    )

    patched = client_for(operator).patch(
        reverse("jobs:detail", args=[job.id]),
        {"status": "CLOSED", "metadata": {"closed_reason": "Filled"}},
        format="json",
    )
    forbidden = client_for(make_user("client", role=User.Role.CLIENT)).get(
        reverse("jobs:detail", args=[job.id])
    )

    assert patched.status_code == 200
    assert patched.json()["status"] == "CLOSED"
    assert patched.json()["metadata"] == {"closed_reason": "Filled"}
    assert forbidden.status_code == 403
