"""Explicit infrastructure-admin operation; never exposed as a public endpoint."""
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.events.services import record_event
from apps.users.models import User


class Command(BaseCommand):
    help = "Grant/revoke a local HTF role for an existing signed-in identity, recording the responsible administrator."

    def add_arguments(self, parser):
        parser.add_argument("--subject", required=True, help="Existing Clerk user subject, never an email guess")
        parser.add_argument("--role", choices=User.Role.values, required=True)
        parser.add_argument("--actor", help="Existing active ADMIN/SUPERADMIN Clerk subject")
        parser.add_argument("--reason", required=True)
        parser.add_argument("--bootstrap", action="store_true", help="First SUPERADMIN only, with no existing active admins")

    @transaction.atomic
    def handle(self, *args, **options):
        if not options["reason"].strip():
            raise CommandError("A reason is required.")
        # Serialize privileged role changes to prevent concurrent first-admin grants.
        users = list(User.objects.select_for_update().order_by("pk"))
        user = next((u for u in users if u.identity_provider == "clerk" and u.identity_provider_subject == options["subject"]), None)
        if user is None:
            raise CommandError("The person must sign in to HTF once before assigning their role.")
        admins = [u for u in users if u.is_active and u.role in {"ADMIN", "SUPERADMIN"}]
        actor = next((u for u in admins if u.identity_provider == "clerk" and u.identity_provider_subject == options["actor"]), None)
        if options["bootstrap"]:
            if admins or options["role"] != "SUPERADMIN" or not user.is_active:
                raise CommandError("Bootstrap is restricted to the first active SUPERADMIN.")
            actor = user
        elif actor is None:
            raise CommandError("An existing active administrator --actor is required.")
        if (options["role"] == "SUPERADMIN" or user.role == "SUPERADMIN") and actor.role != "SUPERADMIN" and not options["bootstrap"]:
            raise CommandError("Only a SUPERADMIN can grant or revoke SUPERADMIN.")
        if user.role == "SUPERADMIN" and options["role"] != "SUPERADMIN" and not any(u.role == "SUPERADMIN" and u.pk != user.pk for u in admins):
            raise CommandError("Cannot remove the last active SUPERADMIN.")
        previous = user.role
        user.role = options["role"]
        user.save(update_fields=["role", "updated_at"])
        record_event(actor=actor, event_type="user.role_changed", summary="Local authorization role changed.", payload={"user_id": user.pk, "from": previous, "to": user.role, "reason": options["reason"][:1000], "bootstrap": options["bootstrap"]}, client_visible=False)
        self.stdout.write(self.style.SUCCESS(f"Updated user {user.pk}: {previous} -> {user.role}. Audit recorded."))
