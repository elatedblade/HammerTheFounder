from apps.users.models import User

from .models import Application


def get_visible_applications(user, *, campaign_id=None):
    applications = Application.objects.select_related(
        "campaign", "campaign__candidate", "job", "job__company", "operator"
    )
    if user.role in {User.Role.OPERATOR, User.Role.ADMIN, User.Role.SUPERADMIN}:
        pass
    else:
        applications = applications.filter(campaign__candidate__user=user)
    if campaign_id is not None:
        applications = applications.filter(campaign_id=campaign_id)
    return applications


def get_visible_application(user, application_id):
    return get_visible_applications(user).filter(pk=application_id).first()
