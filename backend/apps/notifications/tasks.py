from celery import shared_task
from apps.integrations.email.resend import EmailDeliveryError
from .services import deliver_notification


@shared_task(bind=True, max_retries=2, soft_time_limit=45, time_limit=60, ignore_result=True)
def send_notification(self, pk):
    try:
        deliver_notification(pk)
    except EmailDeliveryError:
        raise self.retry(countdown=30 * (self.request.retries + 1))
