from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend

User = get_user_model()


class LoginModelBackend(ModelBackend):
    """
    This is a ModelBacked that allows authentication with the login field.
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None:
            return None
        try:
            user = User.objects.get(login=username)
        except User.DoesNotExist:
            return None
        if user.check_password(password):
            return user
        return None
