from datetime import date
from django.core.management.base import BaseCommand, CommandError
from apps.billing.trials import expire_trials


class Command(BaseCommand):
    help = "Pause unpaid active campaigns whose date-only trial ended before today. Sends nothing."

    def add_arguments(self, parser):
        parser.add_argument("--as-of", help="ISO date, defaults to today in Django timezone")
        parser.add_argument("--limit", type=int, default=500)

    def handle(self, *args, **options):
        try:
            as_of = date.fromisoformat(options["as_of"]) if options["as_of"] else None
        except ValueError as exc:
            raise CommandError("--as-of must be an ISO date") from exc
        if not 1 <= options["limit"] <= 5000:
            raise CommandError("--limit must be between 1 and 5000")
        self.stdout.write(f"Expired {expire_trials(as_of=as_of, limit=options['limit'])} unpaid trial(s).")
