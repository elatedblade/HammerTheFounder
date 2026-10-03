from datetime import timedelta
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from apps.ai.models import AIRun
from apps.notifications.models import Notification
from apps.resumes.models import Resume


class Command(BaseCommand):
    help = "Mark stale supporting jobs interrupted without retrying external actions. Does not send or enqueue anything."

    def add_arguments(self, parser):
        parser.add_argument("--age-minutes", type=int, default=30)

    def handle(self, *args, **options):
        if options["age_minutes"] < 5:
            raise CommandError("Minimum age is 5 minutes.")
        cutoff = timezone.now() - timedelta(minutes=options["age_minutes"])
        ai = AIRun.objects.filter(status="RUNNING", started_at__lt=cutoff).update(status="FAILED", error_code="execution_interrupted", completed_at=timezone.now())
        ai += AIRun.objects.filter(status="QUEUED", created_at__lt=cutoff).update(status="FAILED", error_code="queue_interrupted", completed_at=timezone.now())
        resumes = Resume.objects.filter(parse_status="PROCESSING", parse_started_at__lt=cutoff).update(parse_status="FAILED", parse_error_code="processing_interrupted")
        resumes += Resume.objects.filter(parse_status="QUEUED", updated_at__lt=cutoff).update(parse_status="FAILED", parse_error_code="queue_interrupted")
        notifications = Notification.objects.filter(status="SENDING", started_at__lt=cutoff).update(status="UNKNOWN", error_code="delivery_interrupted")
        notifications += Notification.objects.filter(status="QUEUED", queued_at__lt=cutoff).update(status="UNKNOWN", error_code="queue_interrupted")
        self.stdout.write(f"Reconciled AI={ai}, resumes={resumes}, notifications={notifications}. Unknown emails require provider review before any resend.")
