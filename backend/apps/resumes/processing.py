from datetime import timedelta
from django.db import transaction
from django.http import Http404
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied
from apps.billing.services import Conflict, require_operator
from apps.events.services import record_event
from apps.integrations.storage.s3 import get_resume_storage
from .constants import MAX_RESUME_FILE_SIZE
from .models import Resume
from .parsing import extract_text, DocumentParseError


def visible_resumes(user):
    if not user or not user.is_authenticated or not user.is_active:
        raise PermissionDenied()
    if user.role == "CLIENT":
        return Resume.objects.filter(candidate__user=user)
    require_operator(user)
    from apps.candidates.selectors import get_operational_candidates
    return Resume.objects.filter(candidate__in=get_operational_candidates(user))


def get_resume(user, pk):
    item = visible_resumes(user).filter(pk=pk).first()
    if item is None:
        raise Http404
    return item


def download_resume(*, user, pk):
    item = get_resume(user, pk)
    if item.upload_status != "UPLOADED":
        raise Conflict("Resume upload is not complete.")
    storage = get_resume_storage()
    return {"url": storage.authorize_download(key=item.s3_key, expires_in=300), "expires_in": 300}


def queue_parse(*, user, pk):
    require_operator(user)
    item = get_resume(user, pk)
    if item.upload_status != "UPLOADED":
        raise Conflict("Resume upload is not complete.")
    get_resume_storage()
    with transaction.atomic():
        item = Resume.objects.select_for_update().get(pk=pk)
        if item.parse_status in {"QUEUED", "PROCESSING", "PARSED", "UNSUPPORTED"}:
            return item
        if item.content_type == "application/msword":
            item.parse_status = "UNSUPPORTED"
            item.parse_error_code = "legacy_doc_not_supported"
        else:
            item.parse_status = "QUEUED"
            item.parse_error_code = ""
            transaction.on_commit(lambda: enqueue_parse(str(pk)))
        item.save()
        record_event(event_type="RESUME_PARSE_REQUESTED", actor=user, summary="Resume parsing requested.", payload={"resume_id": str(pk)}, client_visible=False)
    return item


def enqueue_parse(pk):
    from .tasks import parse_resume
    try:
        parse_resume.delay(pk)
    except Exception:
        Resume.objects.filter(pk=pk, parse_status="QUEUED").update(parse_status="FAILED", parse_error_code="queue_unavailable")


def process_resume(pk):
    with transaction.atomic():
        item = Resume.objects.select_for_update().get(pk=pk)
        if item.parse_status == "PROCESSING" and item.parse_started_at < timezone.now() - timedelta(minutes=5):
            item.parse_status = "FAILED"
            item.parse_error_code = "processing_interrupted"
            item.save()
            return
        if item.parse_status != "QUEUED":
            return
        item.parse_status = "PROCESSING"
        item.parse_started_at = timezone.now()
        item.parse_attempts += 1
        item.save()
    try:
        content = get_resume_storage().read_document(key=item.s3_key, max_bytes=MAX_RESUME_FILE_SIZE)
        text = extract_text(content, item.content_type)
    except DocumentParseError as exc:
        Resume.objects.filter(pk=pk, parse_status="PROCESSING").update(parse_status="FAILED", parse_error_code=exc.code)
        return
    except Exception:
        Resume.objects.filter(pk=pk, parse_status="PROCESSING").update(parse_status="FAILED", parse_error_code="storage_or_processing_unavailable")
        return
    Resume.objects.filter(pk=pk, parse_status="PROCESSING").update(parse_status="PARSED", extracted_text=text, parsed_at=timezone.now(), parse_error_code="")
