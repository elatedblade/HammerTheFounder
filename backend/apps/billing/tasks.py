from celery import shared_task
from .trials import expire_trials


@shared_task(soft_time_limit=90, time_limit=120, max_retries=0, ignore_result=True)
def expire_campaign_trials():
    expire_trials()
