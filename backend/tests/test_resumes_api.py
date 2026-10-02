from unittest.mock import Mock

import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from apps.candidates.models import CandidateProfile
from apps.integrations.storage.s3 import (
    StorageNotConfigured,
    StorageObjectMismatch,
    StorageObjectNotFound,
    UploadAuthorization,
)
from apps.resumes.models import Resume
from apps.users.models import User


pytestmark = pytest.mark.django_db


def make_user(subject="candidate", role=User.Role.CLIENT, active=True):
    return User.objects.create_user(
        "clerk", subject, email=f"{subject}@example.com", role=role, is_active=active
    )


def client_for(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


def make_profile(user):
    return CandidateProfile.objects.create(user=user)


def payload(**overrides):
    result = {
        "filename": "resume.pdf",
        "content_type": "application/pdf",
        "file_size": 1024,
    }
    result.update(overrides)
    return result


def fake_storage():
    storage = Mock()
    storage.authorize_upload.return_value = UploadAuthorization(
        url="https://s3.example.test/signed-put",
        headers={"Content-Type": "application/pdf"},
        expires_in=300,
    )
    storage.verify_upload.return_value = None
    return storage


def test_list_returns_only_the_authenticated_candidates_resumes():
    first = make_user("first")
    second = make_user("second")
    first_profile, second_profile = make_profile(first), make_profile(second)
    Resume.objects.create(
        candidate=first_profile,
        s3_key="candidates/1/resumes/one/original.pdf",
        original_filename="one.pdf",
        content_type="application/pdf",
        file_size=100,
    )
    Resume.objects.create(
        candidate=second_profile,
        s3_key="candidates/2/resumes/two/original.pdf",
        original_filename="two.pdf",
        content_type="application/pdf",
        file_size=100,
    )

    response = client_for(first).get(reverse("resumes:candidate-resumes"))

    assert response.status_code == 200
    assert [item["original_filename"] for item in response.json()] == ["one.pdf"]
    assert "s3_key" not in response.json()[0]


def test_post_authorizes_private_put_and_derives_ownership_and_key(monkeypatch):
    user = make_user()
    profile = make_profile(user)
    storage = fake_storage()
    monkeypatch.setattr("apps.resumes.services.get_resume_storage", lambda: storage)

    response = client_for(user).post(
        reverse("resumes:candidate-resumes"),
        payload(candidate_id=999, s3_key="attacker-controlled-key"),
        format="json",
    )

    assert response.status_code == 400
    assert "candidate_id" in response.json()["details"]
    assert "s3_key" in response.json()["details"]
    storage.authorize_upload.assert_not_called()
    assert Resume.objects.count() == 0

    response = client_for(user).post(
        reverse("resumes:candidate-resumes"), payload(), format="json"
    )

    assert response.status_code == 201
    body = response.json()
    resume = Resume.objects.get()
    assert body["id"] == str(resume.id)
    assert body["upload_url"] == "https://s3.example.test/signed-put"
    assert body["upload"]["method"] == "PUT"
    assert resume.candidate_id == profile.id
    assert resume.s3_key == f"candidates/{profile.id}/resumes/{resume.id}/original.pdf"
    storage.authorize_upload.assert_called_once_with(
        key=resume.s3_key,
        content_type="application/pdf",
        file_size=1024,
        expires_in=300,
    )


@pytest.mark.parametrize(
    "invalid",
    [
        {"filename": "../resume.pdf"},
        {"filename": "resume/other.pdf"},
        {"filename": "resume.pdf", "content_type": "text/plain"},
        {"filename": "resume.docx", "content_type": "application/pdf"},
        {"file_size": 10 * 1024 * 1024 + 1},
        {"file_size": 0},
    ],
)
def test_upload_request_rejects_unsafe_or_unsupported_metadata(invalid, monkeypatch):
    user = make_user()
    make_profile(user)
    storage = fake_storage()
    monkeypatch.setattr("apps.resumes.services.get_resume_storage", lambda: storage)

    response = client_for(user).post(
        reverse("resumes:candidate-resumes"), payload(**invalid), format="json"
    )

    assert response.status_code == 400
    assert response.json()["code"] == "VALIDATION_ERROR"
    storage.authorize_upload.assert_not_called()
    assert Resume.objects.count() == 0


def test_unconfigured_storage_returns_stable_503_without_s3_or_metadata(monkeypatch):
    user = make_user()
    make_profile(user)
    storage = Mock()
    storage.authorize_upload.side_effect = AssertionError("must not touch storage")
    monkeypatch.setattr(
        "apps.resumes.services.get_resume_storage",
        Mock(side_effect=StorageNotConfigured()),
    )

    response = client_for(user).post(
        reverse("resumes:candidate-resumes"), payload(), format="json"
    )

    assert response.status_code == 503
    assert response.json() == {
        "code": "STORAGE_NOT_CONFIGURED",
        "message": "Resume storage is not configured.",
        "details": {},
    }
    storage.authorize_upload.assert_not_called()
    assert Resume.objects.count() == 0


def test_original_filename_alias_is_supported_for_existing_client_contract(monkeypatch):
    user = make_user()
    make_profile(user)
    storage = fake_storage()
    monkeypatch.setattr("apps.resumes.services.get_resume_storage", lambda: storage)

    response = client_for(user).post(
        reverse("resumes:candidate-resumes"),
        {
            "original_filename": "resume.docx",
            "content_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "file_size": 2048,
        },
        format="json",
    )

    assert response.status_code == 201
    assert Resume.objects.get().original_filename == "resume.docx"


def test_complete_verifies_and_marks_owned_resume_uploaded_idempotently(monkeypatch):
    user = make_user()
    profile = make_profile(user)
    resume = Resume.objects.create(
        candidate=profile,
        s3_key="candidates/1/resumes/one/original.pdf",
        original_filename="one.pdf",
        content_type="application/pdf",
        file_size=1024,
    )
    storage = fake_storage()
    monkeypatch.setattr("apps.resumes.services.get_resume_storage", lambda: storage)
    url = reverse("resumes:candidate-resume-complete", args=[resume.id])

    response = client_for(user).post(url)

    assert response.status_code == 200
    assert response.json()["upload_status"] == Resume.UploadStatus.UPLOADED
    resume.refresh_from_db()
    assert resume.upload_status == Resume.UploadStatus.UPLOADED
    assert resume.version == 2
    storage.verify_upload.assert_called_once_with(
        key=resume.s3_key,
        content_type="application/pdf",
        file_size=1024,
    )

    retry = client_for(user).post(url)
    assert retry.status_code == 200
    assert retry.json()["upload_status"] == Resume.UploadStatus.UPLOADED
    assert storage.verify_upload.call_count == 1


@pytest.mark.parametrize(
    "storage_error, expected_code",
    [
        (StorageObjectNotFound(), "RESUME_UPLOAD_NOT_FOUND"),
        (StorageObjectMismatch(), "RESUME_UPLOAD_MISMATCH"),
    ],
)
def test_complete_rejects_missing_or_mismatched_object(
    storage_error, expected_code, monkeypatch
):
    user = make_user()
    profile = make_profile(user)
    resume = Resume.objects.create(
        candidate=profile,
        s3_key="candidates/1/resumes/one/original.pdf",
        original_filename="one.pdf",
        content_type="application/pdf",
        file_size=1024,
    )
    storage = fake_storage()
    storage.verify_upload.side_effect = storage_error
    monkeypatch.setattr("apps.resumes.services.get_resume_storage", lambda: storage)

    response = client_for(user).post(
        reverse("resumes:candidate-resume-complete", args=[resume.id])
    )

    assert response.status_code == 409
    assert response.json()["code"] == expected_code
    resume.refresh_from_db()
    assert resume.upload_status == Resume.UploadStatus.PENDING_UPLOAD


def test_complete_cannot_access_another_candidates_resume(monkeypatch):
    owner = make_user("owner")
    other = make_user("other")
    profile = make_profile(owner)
    resume = Resume.objects.create(
        candidate=profile,
        s3_key="candidates/1/resumes/one/original.pdf",
        original_filename="one.pdf",
        content_type="application/pdf",
        file_size=1024,
    )
    storage = fake_storage()
    monkeypatch.setattr("apps.resumes.services.get_resume_storage", lambda: storage)

    response = client_for(other).post(
        reverse("resumes:candidate-resume-complete", args=[resume.id])
    )

    assert response.status_code == 404
    storage.verify_upload.assert_not_called()
