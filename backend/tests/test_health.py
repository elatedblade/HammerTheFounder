import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_health_endpoint_returns_ok(client):
    response = client.get(reverse("health"))

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.django_db
def test_readiness_endpoint_checks_database_and_cache(client):
    response = client.get(reverse("readiness"))

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "checks": {"database": "ok", "redis": "ok"},
    }
    assert response["Cache-Control"] == "no-store"


@pytest.mark.django_db
def test_readiness_endpoint_returns_safe_503_when_dependency_fails(client, monkeypatch):
    secret_connection_detail = "redis://user:password@example.test:6379/1"

    def failed_check():
        raise RuntimeError(secret_connection_detail)

    monkeypatch.setattr("config.urls._check_redis", failed_check)

    response = client.get(reverse("readiness"))

    assert response.status_code == 503
    assert response.json() == {
        "status": "error",
        "checks": {"database": "ok", "redis": "error"},
    }
    assert secret_connection_detail not in response.content.decode()
