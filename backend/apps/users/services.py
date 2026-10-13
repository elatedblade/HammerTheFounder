from django.db import transaction
from rest_framework.exceptions import (
    APIException,
    NotFound,
    PermissionDenied,
    ValidationError,
)

from apps.events.services import record_event

from .models import User


class LastSuperadminConflict(APIException):
    status_code = 409
    default_detail = "Cannot remove the last active SUPERADMIN."
    default_code = "last_superadmin"


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


@transaction.atomic
def change_user_role(*, actor: User, user_id: int, role: str) -> User:
    """Change a local user's role under the active-superadmin safeguards."""
    if role not in User.Role.values:
        raise ValidationError({"role": "Choose a valid user role."})

    # Lock the complete local user set so concurrent role changes cannot both
    # observe the same last-active-superadmin state.
    users = list(User.objects.select_for_update().order_by("pk"))
    locked_actor = next((user for user in users if user.pk == actor.pk), None)
    if (
        locked_actor is None
        or not locked_actor.is_active
        or locked_actor.role != User.Role.SUPERADMIN
    ):
        raise PermissionDenied("An active SUPERADMIN actor is required.")

    target = next((user for user in users if user.pk == user_id), None)
    if target is None:
        raise NotFound("The requested user does not exist.")

    previous = target.role
    if (
        target.is_active
        and previous == User.Role.SUPERADMIN
        and role != User.Role.SUPERADMIN
        and sum(
            user.is_active and user.role == User.Role.SUPERADMIN for user in users
        )
        == 1
    ):
        raise LastSuperadminConflict()

    target.role = role
    target.save(update_fields=("role", "updated_at"))
    record_event(
        actor=locked_actor,
        event_type="user.role_changed",
        summary="Local authorization role changed.",
        payload={"user_id": target.pk, "from": previous, "to": target.role},
        client_visible=False,
    )
    return target
