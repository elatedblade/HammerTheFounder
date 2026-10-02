from django.contrib import admin

from .models import User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = (
        "email",
        "identity_provider",
        "identity_provider_subject",
        "role",
        "is_active",
        "created_at",
    )
    list_filter = ("identity_provider", "role", "is_active", "is_staff")
    search_fields = (
        "email",
        "phone",
        "identity_provider",
        "identity_provider_subject",
    )
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "identity_provider",
                    "identity_provider_subject",
                    "email",
                    "phone",
                )
            },
        ),
        (
            "Authorization",
            {"fields": ("role", "is_active", "is_staff", "groups", "user_permissions")},
        ),
        ("Dates", {"fields": ("created_at", "updated_at")}),
    )
