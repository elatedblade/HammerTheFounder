from django.contrib import admin

from .models import Application


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "candidate",
        "job",
        "campaign",
        "status",
        "created_at",
        "updated_at",
    )
    list_filter = ("status",)
    search_fields = (
        "id",
        "candidate__full_name",
        "candidate__user__email",
        "job__title",
        "job__company__name",
    )
    readonly_fields = ("candidate", "created_at", "updated_at")
