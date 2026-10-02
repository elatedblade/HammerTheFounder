from .models import Resume


def get_own_resumes(user):
    return Resume.objects.filter(candidate__user=user)
