from __future__ import annotations

from typing import Any

from rest_framework.exceptions import ErrorDetail
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler


def api_exception_handler(exc: Exception, context: dict[str, Any]) -> Response | None:
    """Return the stable API error envelope documented by HTF."""

    response = drf_exception_handler(exc, context)
    if response is None:
        return None

    payload = response.data
    if isinstance(payload, dict) and set(payload) == {"detail"}:
        message = _as_message(payload["detail"])
        details: dict[str, Any] = {}
    elif isinstance(payload, dict):
        message = "Request validation failed."
        details = _json_safe(payload)
    else:
        message = "Request failed."
        details = {"errors": _json_safe(payload)}

    response.data = {
        "code": _error_code(response.status_code),
        "message": message,
        "details": details,
    }
    return response


def _error_code(status_code: int) -> str:
    return {
        400: "VALIDATION_ERROR",
        401: "UNAUTHENTICATED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        405: "METHOD_NOT_ALLOWED",
        429: "RATE_LIMITED",
    }.get(status_code, "REQUEST_FAILED")


def _as_message(value: Any) -> str:
    return str(value)


def _json_safe(value: Any) -> Any:
    if isinstance(value, ErrorDetail):
        return str(value)
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    return value
