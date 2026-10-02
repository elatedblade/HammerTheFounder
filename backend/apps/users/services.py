from django.db import transaction

from .models import User


@transaction.atomic
def sync_external_identity(
    identity_provider: str | None = None,
    identity_provider_subject: str | None = None,
    *,
    email: str | None = None,
    phone: str | None = None,
    provider: str | None = None,
    subject: str | None = None,
) -> User:
    """Create or update a local user for an already-validated identity.

    Token validation belongs to the authentication adapter at the application
    boundary. This service only persists the identity attributes it receives;
    role and activation remain local authorization decisions. Repeated calls
    for the same provider/subject converge on one user.
    """
    identity_provider = identity_provider or provider
    identity_provider_subject = identity_provider_subject or subject

    if not identity_provider:
        raise ValueError("The identity provider is required.")
    if not identity_provider_subject:
        raise ValueError("The identity provider subject is required.")

    normalized_email = User.objects.normalize_email(email) if email else ""
    user, _ = User.objects.update_or_create(
        identity_provider=identity_provider,
        identity_provider_subject=identity_provider_subject,
        defaults={
            "email": normalized_email,
            "phone": phone or "",
        },
    )

    # Do not permit a password to be introduced through an existing local row.
    if user.has_usable_password():
        user.set_unusable_password()
        user.save(update_fields=("password", "updated_at"))

    return user
