from io import StringIO

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from rest_framework.test import APIClient

from apps.events.models import Event
from apps.users.models import User
from config.observability import scrub_event


def test_telemetry_removes_sensitive_context():
    result = scrub_event({"request": {"data": "private"}, "user": {"email": "private"}, "extra": {"token": "private"}, "breadcrumbs": [], "exception": {"values": [{"value": "private", "stacktrace": {"frames": [{"vars": {"secret": "private"}, "lineno": 1}]}}]}}, {})
    assert not {"request", "user", "extra", "breadcrumbs"}.intersection(result)
    assert "private" not in str(result)
    assert result["exception"]["values"][0]["stacktrace"]["frames"][0]["lineno"] == 1


def test_unauthenticated_api_responses_are_not_cached():
    response = APIClient().get("/api/v1/me/")
    assert response.status_code == 401
    assert response["Cache-Control"] == "no-store, private"


@pytest.mark.django_db
def test_role_bootstrap_and_grant_are_explicit_and_audited():
    first = User.objects.create_user("clerk", "bootstrap-fixture")
    second = User.objects.create_user("clerk", "operator-fixture")
    call_command("set_htf_role", subject=first.identity_provider_subject, role="SUPERADMIN", bootstrap=True, reason="Synthetic bootstrap test", stdout=StringIO())
    call_command("set_htf_role", subject=second.identity_provider_subject, role="OPERATOR", actor=first.identity_provider_subject, reason="Synthetic grant test", stdout=StringIO())
    second.refresh_from_db()
    assert second.role == "OPERATOR"
    assert Event.objects.filter(event_type="user.role_changed", client_visible=False).count() == 2
    with pytest.raises(CommandError):
        call_command("set_htf_role", subject=second.identity_provider_subject, role="SUPERADMIN", bootstrap=True, reason="Cannot bootstrap twice", stdout=StringIO())
    with pytest.raises(CommandError):
        call_command("set_htf_role", subject=first.identity_provider_subject, role="CLIENT", actor=first.identity_provider_subject, reason="Cannot remove last superadmin", stdout=StringIO())
