import pytest
from django.test import Client


@pytest.mark.django_db
def test_allowed_frontend_origin_receives_cors_preflight_headers(settings):
    settings.CORS_ALLOWED_ORIGINS = ["http://localhost:3000"]

    response = Client().options(
        "/api/v1/me/",
        HTTP_ORIGIN="http://localhost:3000",
        HTTP_ACCESS_CONTROL_REQUEST_METHOD="GET",
        HTTP_ACCESS_CONTROL_REQUEST_HEADERS="authorization,content-type",
    )

    assert response.status_code == 200
    assert response["Access-Control-Allow-Origin"] == "http://localhost:3000"
    assert "authorization" in response["Access-Control-Allow-Headers"]


@pytest.mark.django_db
def test_unlisted_origin_does_not_receive_cors_headers(settings):
    settings.CORS_ALLOWED_ORIGINS = ["http://localhost:3000"]

    response = Client().options(
        "/api/v1/me/",
        HTTP_ORIGIN="http://malicious.example",
        HTTP_ACCESS_CONTROL_REQUEST_METHOD="GET",
        HTTP_ACCESS_CONTROL_REQUEST_HEADERS="authorization",
    )

    assert response.status_code == 200
    assert "Access-Control-Allow-Origin" not in response
