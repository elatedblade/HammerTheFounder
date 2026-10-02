from apps.users.models import User

from .models import Job


def _can_access_jobs(user):
    return bool(
        user
        and user.is_authenticated
        and user.is_active
        and user.role
        in {User.Role.OPERATOR, User.Role.ADMIN, User.Role.SUPERADMIN}
    )


def get_visible_jobs(user, *, company_id=None, status=None, external_source=None):
    if not _can_access_jobs(user):
        return Job.objects.none()
    jobs = Job.objects.select_related("company")
    if company_id:
        jobs = jobs.filter(company_id=company_id)
    if status:
        jobs = jobs.filter(status=status)
    if external_source:
        jobs = jobs.filter(external_source=external_source.casefold())
    return jobs


def get_visible_job(user, job_id):
    return get_visible_jobs(user).filter(pk=job_id).first()
