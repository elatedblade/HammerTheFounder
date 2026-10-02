from apps.users.models import User

from .models import Company


def _can_access_companies(user):
    return bool(
        user
        and user.is_authenticated
        and user.is_active
        and user.role
        in {User.Role.OPERATOR, User.Role.ADMIN, User.Role.SUPERADMIN}
    )


def get_visible_companies(user):
    if not _can_access_companies(user):
        return Company.objects.none()
    return Company.objects.all()


def get_visible_company(user, company_id):
    return get_visible_companies(user).filter(pk=company_id).first()
