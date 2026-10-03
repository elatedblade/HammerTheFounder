from celery import shared_task
from .services import execute_run


@shared_task(soft_time_limit=50, time_limit=65, ignore_result=True, max_retries=0)
def execute_ai_run(pk):
    execute_run(pk)
