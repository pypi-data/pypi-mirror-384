from django.utils.deprecation import MiddlewareMixin
from django.utils import translation
from django.conf import settings


class SetLanguageMiddleware(MiddlewareMixin):
    @staticmethod
    def process_request(request):
        if hasattr(request.user, 'language_code'):
            user_language = request.user.language_code or settings.LANGUAGE_CODE
            translation.activate(user_language)
