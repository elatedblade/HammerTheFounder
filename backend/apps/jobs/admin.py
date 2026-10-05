from django.contrib import admin

from .models import Job


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "company",
        "external_source",
        "external_id",
        "status",
        "last_seen_at",
    )
    list_filter = ("status", "external_source", "employment_type")
    search_fields = (
        "title",
        "company__name",
        "external_id",
        "canonical_url",
        "fingerprint",
    )
    readonly_fields = ("id", "first_seen_at", "last_seen_at")
