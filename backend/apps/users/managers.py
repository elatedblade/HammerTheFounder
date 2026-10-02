from django.contrib.auth.base_user import BaseUserManager


class UserManager(BaseUserManager):
    """Create local users without ever assigning a usable password."""

    use_in_migrations = True

    def sync_external_identity(
        self,
        *,
        provider: str,
        subject: str,
        email: str = "",
        phone: str = "",
    ):
        """Compatibility entrypoint for callers at the auth boundary."""
        from .services import sync_external_identity

        return sync_external_identity(
            identity_provider=provider,
            identity_provider_subject=subject,
            email=email,
            phone=phone,
        )

    def create_user(
        self,
        identity_provider: str,
        identity_provider_subject: str,
        **extra_fields,
    ):
        if not identity_provider:
            raise ValueError("The identity provider is required.")
        if not identity_provider_subject:
            raise ValueError("The identity provider subject is required.")

        email = extra_fields.get("email")
        if email:
            extra_fields["email"] = self.normalize_email(email)

        user = self.model(
            identity_provider=identity_provider,
            identity_provider_subject=identity_provider_subject,
            **extra_fields,
        )
        user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(
        self,
        identity_provider: str,
        identity_provider_subject: str,
        **extra_fields,
    ):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("role", "SUPERADMIN")

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(
            identity_provider,
            identity_provider_subject,
            **extra_fields,
        )
