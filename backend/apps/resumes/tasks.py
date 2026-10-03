from celery import shared_task
from .processing import process_resume


@shared_task(soft_time_limit=90, time_limit=120, max_retries=0, ignore_result=True)
def parse_resume(pk):
    process_resume(pk)
