import json
from unittest.mock import Mock
import pytest
from pydantic import ValidationError
from apps.ai.schemas import JobMatch, QA
from apps.integrations.ai.omniroute import generate, GatewayError, AINotConfigured, configuration


def test_typed_match_rejects_out_of_range_or_extra_fields():
    with pytest.raises(ValidationError):
        JobMatch.model_validate({"score": 101, "reasons": [], "gaps": []})
    with pytest.raises(ValidationError):
        QA.model_validate({"passed": True, "issues": [], "recommendations": [], "send_email": True})


def test_gateway_rejects_nonlocal_plaintext_config(settings):
    settings.OMNIROUTE_BASE_URL = "http://gateway.example.test/v1"
    settings.OMNIROUTE_API_KEY = "test-key"
    settings.OMNIROUTE_MODEL = "configured-model"
    with pytest.raises(AINotConfigured):
        configuration()


def test_gateway_bounded_request_validates_output_and_safe_usage(settings, monkeypatch):
    import httpx
    settings.OMNIROUTE_BASE_URL = "http://localhost:20128/v1"
    settings.OMNIROUTE_API_KEY = "test-key"
    settings.OMNIROUTE_MODEL = "configured-model"
    requests = []
    def handler(request):
        requests.append(request)
        return httpx.Response(200, json={"id": "completion", "object": "chat.completion", "created": 1, "model": "configured-model", "choices": [{"index": 0, "message": {"role": "assistant", "content": json.dumps({"score": 70, "reasons": ["Relevant experience"], "gaps": []})}, "finish_reason": "stop"}], "usage": {"prompt_tokens": 7, "completion_tokens": 5, "total_tokens": 12}})
    monkeypatch.setattr("apps.integrations.ai.omniroute.make_http_client", lambda: httpx.AsyncClient(transport=httpx.MockTransport(handler), follow_redirects=False))
    result, metadata = generate(capability="job_match", input_data={"profile": "Engineer"}, schema=JobMatch)
    assert result["score"] == 70 and metadata["usage"]["total_tokens"] == 12
    assert len(requests) == 1
    payload = json.loads(requests[0].content)
    assert payload["max_completion_tokens"] == 2048 and not payload.get("tools")
    assert payload["response_format"]["type"] == "json_schema"
    assert str(requests[0].url) == "http://localhost:20128/v1/chat/completions"


def test_gateway_invalid_output_returns_safe_code(settings, monkeypatch):
    import httpx
    settings.OMNIROUTE_BASE_URL = "http://localhost:20128/v1"
    settings.OMNIROUTE_API_KEY = "test-key"
    settings.OMNIROUTE_MODEL = "configured-model"
    requests = []
    def handler(request):
        requests.append(request)
        return httpx.Response(200, json={"id": "bad", "object": "chat.completion", "created": 1, "model": "configured-model", "choices": [{"index": 0, "message": {"role": "assistant", "content": "private invalid text"}, "finish_reason": "stop"}]})
    monkeypatch.setattr("apps.integrations.ai.omniroute.make_http_client", lambda: httpx.AsyncClient(transport=httpx.MockTransport(handler)))
    with pytest.raises(GatewayError) as error:
        generate(capability="qa", input_data={}, schema=QA)
    assert error.value.code == "invalid_model_output"
    assert len(requests) == 1  # No SDK retries or framework repair completions.
