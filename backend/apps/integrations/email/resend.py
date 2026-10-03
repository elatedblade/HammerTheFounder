import json
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request
from apps.integrations.ai.http import urlopen

from django.conf import settings
from rest_framework.exceptions import APIException


class EmailNotConfigured(APIException):
    status_code = 503
    default_code = "email_not_configured"
    default_detail = "Transactional email is not configured."


class EmailDeliveryError(Exception):
    def __init__(self, code, retryable=False):
        self.code = code
        self.retryable = retryable


def configuration():
    key = getattr(settings, "RESEND_API_KEY", os.getenv("RESEND_API_KEY", ""))
    sender = getattr(settings, "RESEND_FROM_EMAIL", os.getenv("RESEND_FROM_EMAIL", ""))
    if not key or not sender:
        raise EmailNotConfigured()
    return key, sender


def deliver(*, recipient, subject, body, idempotency_key):
    key, sender = configuration()
    request = Request("https://api.resend.com/emails", data=json.dumps({"from": sender, "to": [recipient], "subject": subject, "text": body}).encode(), headers={"Authorization": "Bearer " + key, "Content-Type": "application/json", "Idempotency-Key": idempotency_key}, method="POST")
    try:
        with urlopen(request, timeout=15) as response:
            data = json.loads(response.read(65537))
        if not isinstance(data.get("id"), str):
            raise EmailDeliveryError("invalid_provider_response")
        return data["id"]
    except HTTPError as exc:
        raise EmailDeliveryError("provider_http_" + str(exc.code), exc.code == 429 or exc.code >= 500) from exc
    except (URLError, TimeoutError, OSError) as exc:
        raise EmailDeliveryError("provider_unavailable", True) from exc
    except (ValueError, KeyError) as exc:
        raise EmailDeliveryError("invalid_provider_response") from exc
