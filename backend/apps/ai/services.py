import time
from datetime import timedelta
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from apps.billing.services import require_operator, get_visible_campaign
from apps.events.services import record_event
from apps.integrations.ai.omniroute import configuration, generate, GatewayError
from .models import AIRun
from .schemas import OUTPUT_SCHEMAS
from .inputs import validate_input, canonical_input, AGENT_VERSION, PROMPT_VERSION


def create_run(*, user, data):
    require_operator(user)
    campaign = get_visible_campaign(user, data["campaign"])
    config = configuration()
    input_data = validate_input(data["capability"], data["input"])
    try:
        _, sources = canonical_input(campaign, data["capability"], input_data)
    except GatewayError as exc:
        raise ValidationError({"input": exc.code}) from exc
    with transaction.atomic():
        run = AIRun.objects.create(campaign=campaign, capability=data["capability"], input_json=input_data, created_by=user, model_name=config["OMNIROUTE_MODEL"], agent_version=AGENT_VERSION, prompt_version=PROMPT_VERSION, source_references=sources)
        record_event(campaign=campaign, actor=user, event_type="AI_REQUESTED", summary="AI proposal requested for human review.", payload={"run_id": str(run.pk), "capability": run.capability}, client_visible=False)
        transaction.on_commit(lambda: enqueue_run(str(run.pk)))
    return run


def enqueue_run(pk):
    from .tasks import execute_ai_run
    try:
        execute_ai_run.delay(pk)
    except Exception:
        AIRun.objects.filter(pk=pk, status="QUEUED").update(status="FAILED", error_code="queue_unavailable", completed_at=timezone.now())


def execute_run(pk):
    with transaction.atomic():
        run = AIRun.objects.select_for_update().get(pk=pk)
        if run.status == "RUNNING" and run.started_at < timezone.now() - timedelta(minutes=5):
            run.status = "FAILED"
            run.error_code = "execution_interrupted"
            run.completed_at = timezone.now()
            run.save()
            return
        if run.status != "QUEUED":
            return
        run.status = "RUNNING"
        run.started_at = timezone.now()
        run.attempts += 1
        run.save()
    start = time.monotonic()
    try:
        require_operator(run.created_by)
        campaign = get_visible_campaign(run.created_by, run.campaign_id)
        input_data, sources = canonical_input(campaign, run.capability, validate_input(run.capability, run.input_json))
        AIRun.objects.filter(pk=pk, status="RUNNING").update(source_references=sources, agent_version=AGENT_VERSION, prompt_version=PROMPT_VERSION)
        result, metadata = generate(capability=run.capability, input_data=input_data, schema=OUTPUT_SCHEMAS[run.capability])
    except GatewayError as exc:
        AIRun.objects.filter(pk=pk, status="RUNNING").update(status="FAILED", error_code=exc.code, completed_at=timezone.now(), duration_ms=int((time.monotonic() - start) * 1000))
        return
    except Exception:
        AIRun.objects.filter(pk=pk, status="RUNNING").update(status="FAILED", error_code="execution_error", completed_at=timezone.now())
        return
    with transaction.atomic():
        run = AIRun.objects.select_for_update().get(pk=pk)
        if run.status != "RUNNING":
            return
        run.status = "SUCCEEDED"
        run.result = {"proposal": result, "requires_human_review": True}
        run.model_name = metadata["model"]
        run.provider_request_id = metadata["request_id"]
        run.usage_json = metadata["usage"]
        run.duration_ms = int((time.monotonic() - start) * 1000)
        run.completed_at = timezone.now()
        run.save()
        record_event(campaign=run.campaign, actor=run.created_by, event_type="AI_PROPOSAL_READY", summary="AI proposal ready for human review.", payload={"run_id": str(run.pk)}, client_visible=False)
