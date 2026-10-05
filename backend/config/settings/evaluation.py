"""Private, domain-free EC2 evaluation through SSH-forwarded localhost only.

This is not a public HTTP production mode. Security groups must not expose the
application ports, and SSH access must be restricted to authorized evaluators.
"""
import os

from django.core.exceptions import ImproperlyConfigured

from .base import *  # noqa: F403

DEBUG = False
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "")
if len(SECRET_KEY) < 50 or SECRET_KEY.startswith(("django-insecure", "replace-this")):
    raise ImproperlyConfigured("Evaluation requires a unique secret of at least 50 characters.")
if DATABASES["default"]["ENGINE"] != "django.db.backends.postgresql":
    raise ImproperlyConfigured("Evaluation requires PostgreSQL DATABASE_URL.")
ALLOWED_HOSTS = ["localhost", "127.0.0.1", "[::1]"]
CORS_ALLOWED_ORIGINS = ["http://localhost:3000", "http://localhost:3001"]
CSRF_TRUSTED_ORIGINS = CORS_ALLOWED_ORIGINS
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
SECURE_REFERRER_POLICY = "same-origin"

CACHES = {"default": {
    "BACKEND": "django.core.cache.backends.redis.RedisCache",
    "LOCATION": os.getenv("CACHE_URL", "redis://redis:6379/1"),
}}
REST_FRAMEWORK = {
    **REST_FRAMEWORK,
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {"anon": "60/min", "user": "300/min"},
}
