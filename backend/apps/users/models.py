from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models

from .managers import UserManager


class User(AbstractBaseUser, PermissionsMixin):
    """Local authorization record mapped to a managed external identity."""

    class Role(models.TextChoices):
        CLIENT = "CLIENT", "Client"
        OPERATOR = "OPERATOR", "Operator"
        ADMIN = "ADMIN", "Admin"
        SUPERADMIN = "SUPERADMIN", "Superadmin"

    identity_provider = models.CharField(max_length=64)
    identity_provider_subject = models.CharField(max_length=255)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=32, blank=True)
    role = models.CharField(
        max_length=16,
        choices=Role.choices,
        default=Role.CLIENT,
    )
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    # The external identity pair, rather than a password or username, is the
    # application's identity boundary. The local primary key is used only to
    # satisfy Django's single USERNAME_FIELD contract; no password login is
    # exposed by this app.
    USERNAME_FIELD = "id"
    REQUIRED_FIELDS = []

    class Meta:
        ordering = ("-created_at",)
        constraints = [
            models.UniqueConstraint(
                fields=("identity_provider", "identity_provider_subject"),
                name="users_provider_subject_unique",
            ),
        ]

    def __str__(self):
        return self.email or f"{self.identity_provider}:{self.identity_provider_subject}"
