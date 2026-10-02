from django.contrib import admin

from .models import Campaign


@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    list_display = ("id", "candidate", "plan", "status", "billing_status", "version")
    list_filter = ("plan", "status", "billing_status")
    search_fields = ("candidate__user__email", "candidate__full_name")
