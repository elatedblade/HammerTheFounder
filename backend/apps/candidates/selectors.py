from .models import CandidateProfile


def get_own_profile(user):
    """Return the current user's profile without creating one as a side effect."""
    return CandidateProfile.objects.filter(user=user).first()
