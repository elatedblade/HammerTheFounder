"""Production settings with explicit secret and database requirements."""

import os
from urllib.parse import urlparse

from django.core.exceptions import ImproperlyConfigured

from .base import *  # noqa: F403
from .base import database_from_url

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY")
if not SECRET_KEY:
    raise ImproperlyConfigured("DJANGO_SECRET_KEY must be set in production.")

DEBUG = False

configured_hosts = os.getenv("DJANGO_ALLOWED_HOSTS", "")
ALLOWED_HOSTS = [host.strip() for host in configured_hosts.split(",") if host.strip()]
if not ALLOWED_HOSTS:
    raise ImproperlyConfigured("DJANGO_ALLOWED_HOSTS must contain at least one host.")

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ImproperlyConfigured("DATABASE_URL must be set in production.")
DATABASES = {"default": database_from_url(DATABASE_URL)}
if DATABASES["default"]["ENGINE"] != "django.db.backends.postgresql":
    raise ImproperlyConfigured("Production requires PostgreSQL.")
if len(SECRET_KEY) < 50 or SECRET_KEY.startswith(("django-insecure", "replace-this")):
    raise ImproperlyConfigured("Production requires a strong, unique Django secret of 50+ characters.")


def required_cache_url() -> str:
    """Return a validated production Redis URL without a topology fallback."""
    cache_url = os.getenv("CACHE_URL", "").strip()
    if not cache_url:
        raise ImproperlyConfigured("CACHE_URL must be set in production.")

    parsed = urlparse(cache_url)
    if parsed.scheme not in {"redis", "rediss"} or not parsed.hostname:
        raise ImproperlyConfigured("CACHE_URL must be a valid redis:// or rediss:// URL.")
    return cache_url

SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
CSRF_TRUSTED_ORIGINS = [v.strip() for v in os.getenv("CSRF_TRUSTED_ORIGINS", "").split(",") if v.strip()]
# Enable only behind a trusted proxy that strips incoming forwarded headers.
if os.getenv("TRUST_PROXY_SSL_HEADER", "false").lower() == "true":
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_REFERRER_POLICY = "same-origin"

# Shared Redis-backed request counters across Gunicorn workers. Complement these
# soft DRF limits with hard rate/body limits on the trusted TLS reverse proxy.
CACHE_URL = required_cache_url()
CACHES = {"default": {"BACKEND": "django.core.cache.backends.redis.RedisCache", "LOCATION": CACHE_URL}}
REST_FRAMEWORK = {
    **REST_FRAMEWORK,
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {"anon": "60/min", "user": "300/min"},
}

SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
X_FRAME_OPTIONS = "DENY"
