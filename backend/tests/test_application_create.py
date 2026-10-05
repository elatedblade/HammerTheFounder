import pytest
from tests.test_operations_api import workspace, api, BASE
from apps.applications.models import Application
from apps.companies.models import Company
from apps.jobs.models import Job
from apps.events.models import Event

pytestmark = pytest.mark.django_db


def payload(campaign, **job):
    return {"campaign": str(campaign.pk), "new_job": {"company_name": "New Company", "title": "Engineer", **job}}


def test_one_save_creates_dependencies_and_unsent_record(workspace):
    _, operator, _, _, _, campaign, *_ = workspace
    response = api(operator).post(BASE + "applications/create/", payload(campaign), format="json")
    assert response.status_code == 201
    record = Application.objects.get(pk=response.json()["id"])
    assert record.status == "SAVED" and record.submitted_at is None
    assert record.job.company.name == "New Company"
    assert campaign.human_tasks.filter(task_type="APPLICATION_FIT_REVIEW").count() == 1
    assert api(operator).post(BASE + "applications/create/", payload(campaign), format="json").status_code == 409
    assert Company.objects.filter(name="New Company").count() == 1


def test_invalid_job_rolls_back_company_and_audit(workspace):
    _, operator, _, _, _, campaign, *_ = workspace
    before = (Company.objects.count(), Job.objects.count(), Event.objects.count())
    response = api(operator).post(BASE + "applications/create/", payload(campaign, canonical_url="invalid"), format="json")
    assert response.status_code == 400
    assert (Company.objects.count(), Job.objects.count(), Event.objects.count()) == before


def test_permissions_closed_campaign_and_existing_job(workspace):
    owner, operator, _, other, _, campaign, _, job, _ = workspace
    route = BASE + "applications/create/"
    assert api(owner).post(route, payload(campaign), format="json").status_code == 403
    assert api(other).post(route, payload(campaign), format="json").status_code == 404
    assert not Company.objects.filter(name="New Company").exists()
    response = api(operator).post(route, {"campaign": str(campaign.pk), "job": str(job.pk)}, format="json")
    assert response.status_code == 201
    campaign.status = "COMPLETED"
    campaign.save()
    assert api(operator).post(route, payload(campaign), format="json").status_code == 409
    assert not Company.objects.filter(name="New Company").exists()


def test_reuses_existing_company_and_rejects_closed_job(workspace):
    _, operator, _, _, _, campaign, company, job, _ = workspace
    response = api(operator).post(BASE + "applications/create/", payload(campaign, company_name="acme"), format="json")
    assert response.status_code == 201
    assert Application.objects.get(pk=response.json()["id"]).job.company_id == company.pk
    job.status = "CLOSED"
    job.save()
    assert api(operator).post(BASE + "applications/create/", {"campaign": str(campaign.pk), "job": str(job.pk)}, format="json").status_code == 409
