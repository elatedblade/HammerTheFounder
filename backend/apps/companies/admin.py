from django.contrib import admin

from .models import Company


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ("name", "website", "industry", "location", "created_at")
    search_fields = ("name", "website", "industry", "location")
    list_filter = ("industry",)
    readonly_fields = ("id", "identity_key", "created_at", "updated_at")
