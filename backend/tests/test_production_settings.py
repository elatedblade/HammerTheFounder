import importlib

import pytest
from django.core.exceptions import ImproperlyConfigured


@pytest.fixture
def production_settings(monkeypatch):
    monkeypatch.setenv("DJANGO_SECRET_KEY", "s" * 64)
    monkeypatch.setenv("DJANGO_ALLOWED_HOSTS", "api.example.test")
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:password@db.example.test:5432/htf")
    monkeypatch.setenv("CACHE_URL", "rediss://cache.example.test:6380/1")
    return importlib.import_module("config.settings.production")


def test_production_cache_url_is_explicit_and_used(production_settings):
    assert production_settings.CACHE_URL == "rediss://cache.example.test:6380/1"
    assert production_settings.CACHES["default"]["LOCATION"] == production_settings.CACHE_URL


def test_production_cache_url_rejects_missing_or_non_redis(monkeypatch, production_settings):
    monkeypatch.delenv("CACHE_URL")
    with pytest.raises(ImproperlyConfigured, match="CACHE_URL must be set"):
        production_settings.required_cache_url()

    monkeypatch.setenv("CACHE_URL", "http://cache.example.test")
    with pytest.raises(ImproperlyConfigured, match="valid redis:// or rediss://"):
        production_settings.required_cache_url()
