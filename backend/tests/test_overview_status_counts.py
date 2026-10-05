"""Overview cards count current states, not overlapping lifecycle history."""
import pytest
from django.utils import timezone
from apps.campaigns.models import Campaign
from apps.candidates.models import CandidateProfile
from apps.outreach.models import Outreach
from apps.outreach.stages import STAGE_STATUSES
from tests.test_operations_api import workspace, api, BASE, user

pytestmark = pytest.mark.django_db


def test_sent_to_responded_moves_one_record_between_overview_cards(workspace):
    owner, operator, admin, _, _, campaign, _, _, contact = workspace
    record = Outreach.objects.create(campaign=campaign, contact=contact, channel="EMAIL", body="Synthetic outreach")
    route = BASE + f"outreach/{record.pk}/transition/"
    initial = api(owner).get(BASE + "dashboard/").json()["outreach"]
    assert initial["total"] == 1 and initial["stage_counts"] == {"SENT": 0, "RESPONDED": 0}
    for status, sent, responded in [("SENT", 1, 0), ("REPLIED", 0, 1)]:
        response = api(admin).post(route, {"status": status}, format="json")
        assert response.status_code == 200
        assert response.json()["id"] == str(record.pk)
        assert Outreach.objects.filter(campaign=campaign).count() == 1
        for viewer in [owner, operator, admin]:
            for endpoint in ["dashboard/", f"campaigns/{campaign.pk}/metrics/"]:
                totals = api(viewer).get(BASE + endpoint).json()["outreach"]
                assert totals["total"] == 1
                assert totals["sent"] == sent
                assert totals["replies"] == totals["replied"] == responded
                assert totals["sent"] + totals["replies"] == 1
                assert totals["stage_counts"] == {"SENT": sent, "RESPONDED": responded}
                assert totals["sent_lifetime"] == 1
                assert totals["replied_lifetime"] == responded
                assert totals["by_status"][status] == 1
            for stage, count in [("SENT", sent), ("RESPONDED", responded)]:
                rows = api(viewer).get(BASE + "outreach/", {"stage": stage}).json()
                assert len(rows) == count
                if count:
                    assert rows[0]["id"] == str(record.pk)
    record.refresh_from_db()
    assert record.sent_at and record.reply_at
    assert api(operator).post(route, {"status": "REPLIED"}, format="json").status_code == 409
    assert Outreach.objects.filter(campaign=campaign).count() == 1


def test_closed_outreach_does_not_remain_in_previous_status_counts(workspace):
    owner, operator, _, _, _, campaign, _, _, contact = workspace
    record = Outreach.objects.create(campaign=campaign, contact=contact, channel="EMAIL", body="Synthetic outreach")
    route = BASE + f"outreach/{record.pk}/transition/"
    for status in ["SENT", "DELIVERED", "REPLIED", "CLOSED"]:
        assert api(operator).post(route, {"status": status}, format="json").status_code == 200
    totals = api(owner).get(BASE + "dashboard/").json()["outreach"]
    assert totals["total"] == 1
    assert totals["sent"] == totals["replies"] == totals["delivered"] == 0
    assert totals["by_status"]["CLOSED"] == 1
    assert totals["stage_counts"] == {"SENT": 0, "RESPONDED": 0}
    assert totals["sent_lifetime"] == totals["replied_lifetime"] == totals["delivered_lifetime"] == 1
    record.refresh_from_db()
    assert record.sent_at and record.delivered_at and record.reply_at


@pytest.mark.parametrize("status", Outreach.Status.values)
def test_every_current_state_agrees_with_grouped_and_exact_lists(workspace, status):
    owner, operator, admin, _, _, campaign, _, _, contact = workspace
    # Old evidence must not keep a record in an earlier active bucket.
    now = timezone.now()
    record = Outreach.objects.create(campaign=campaign, contact=contact, status=status,
                                     sent_at=now, delivered_at=now, reply_at=now)
    expected = {stage: int(status in statuses) for stage, statuses in STAGE_STATUSES.items()}
    for identity in (owner, operator, admin):
        client = api(identity)
        for endpoint in ("dashboard/", f"campaigns/{campaign.pk}/metrics/"):
            totals = client.get(BASE + endpoint).json()["outreach"]
            assert totals["total"] == 1
            assert totals["stage_counts"] == expected
            assert totals["sent"] == expected["SENT"]
            assert totals["replies"] == totals["replied"] == expected["RESPONDED"]
            assert totals["by_status"] == {key: int(key == status) for key in Outreach.Status.values}
            assert totals["sent_lifetime"] == totals["replied_lifetime"] == 1
        for stage, count in expected.items():
            for endpoint in ("outreach/", f"campaigns/{campaign.pk}/outreach/"):
                rows = client.get(BASE + endpoint, {"stage": stage}).json()
                assert len(rows) == count
                if count:
                    assert rows[0]["id"] == str(record.pk)
        for exact in Outreach.Status.values:
            assert len(client.get(BASE + "outreach/", {"status": exact}).json()) == int(exact == status)
    record.refresh_from_db()
    assert record.status == status and record.sent_at == record.delivered_at == record.reply_at == now


def test_stage_filters_preserve_scope_intersections_and_validation(workspace):
    owner, operator, admin, other, _, campaign, _, _, contact = workspace
    record = Outreach.objects.create(campaign=campaign, contact=contact, status="DELIVERED")
    outsider = user("outreach-stage-outsider")
    hidden_profile = CandidateProfile.objects.create(user=outsider, full_name="Hidden")
    hidden_campaign = Campaign.objects.create(candidate=hidden_profile, plan="FULL_THROTTLE", status="ACTIVE", assigned_to=other)
    hidden = Outreach.objects.create(campaign=hidden_campaign, contact=contact, status="POSITIVE_REPLY")
    for identity in (owner, operator):
        client = api(identity)
        assert client.get(BASE + "outreach/", {"stage": "RESPONDED"}).json() == []
        assert client.get(BASE + "outreach/", {"stage": "SENT", "status": "SENT"}).json() == []
        rows = client.get(BASE + "outreach/", {"stage": "SENT", "status": "DELIVERED"}).json()
        assert [row["id"] for row in rows] == [str(record.pk)]
        assert client.get(BASE + "outreach/", {"stage": "RESPONDED", "campaign": str(hidden_campaign.pk)}).status_code == 404
        assert client.get(BASE + f"campaigns/{hidden_campaign.pk}/outreach/", {"stage": "RESPONDED"}).status_code == 404
        assert client.get(BASE + f"outreach/{hidden.pk}/").status_code == 404
        assert client.get(BASE + f"campaigns/{hidden_campaign.pk}/metrics/").status_code == 404
        metrics = client.get(BASE + "dashboard/").json()["outreach"]
        assert metrics["total"] == 1 and metrics["stage_counts"] == {"SENT": 1, "RESPONDED": 0}
        for invalid in ("", "sent", "REPLIED", "UNKNOWN"):
            result = client.get(BASE + "outreach/", {"stage": invalid})
            assert result.status_code == 400 and "stage" in result.json()["details"]
    assert api(outsider).get(BASE + "outreach/", {"stage": "SENT"}).json() == []
    assert api(other).get(BASE + "dashboard/").json()["outreach"]["stage_counts"] == {"SENT": 0, "RESPONDED": 1}
    assert api(admin).get(BASE + "dashboard/").json()["outreach"]["stage_counts"] == {"SENT": 1, "RESPONDED": 1}


def test_bounced_record_leaves_active_sent_bucket(workspace):
    owner, _, admin, _, _, campaign, _, _, contact = workspace
    record = Outreach.objects.create(campaign=campaign, contact=contact, body="Synthetic message")
    route = BASE + f"outreach/{record.pk}/transition/"
    assert api(admin).post(route, {"status": "SENT"}, format="json").status_code == 200
    assert api(admin).post(route, {"status": "BOUNCED", "notes": "Synthetic bounce"}, format="json").status_code == 200
    totals = api(owner).get(BASE + "dashboard/").json()["outreach"]
    assert totals["total"] == totals["bounced"] == totals["sent_lifetime"] == 1
    assert totals["stage_counts"] == {"SENT": 0, "RESPONDED": 0}
    assert totals["sent"] == totals["replies"] == totals["replied_lifetime"] == 0
    record.refresh_from_db()
    assert record.sent_at and record.bounced_at and record.reply_at is None
