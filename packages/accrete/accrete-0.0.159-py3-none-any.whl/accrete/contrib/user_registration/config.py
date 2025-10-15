import logging
from django.conf import settings
from django.utils.translation import gettext_lazy as _

_logger = logging.getLogger(__name__)

ACCRETE_USER_REGISTRATION_MAIL_FROM_NAME = getattr(
    settings, 'ACCRETE_USER_REGISTRATION_MAIL_FROM_NAME',
    False
)

ACCRETE_USER_REGISTRATION_TEMPLATE_NAME = getattr(
    settings, 'ACCRETE_USER_REGISTRATION_TEMPLATE_NAME',
    'user_registration/mail_templates/confirmation_mail.html'
)

ACCRETE_USER_REGISTRATION_MAIL_SUBJECT = getattr(
    settings, 'ACCRETE_USER_REGISTRATION_MAIL_SUBJECT',
    _('Registration Confirmation')
)

ACCRETE_USER_REGISTRATION_ALLOWED = getattr(
    settings, 'ACCRETE_USER_REGISTRATION_ALLOWED', True
)

if not ACCRETE_USER_REGISTRATION_MAIL_FROM_NAME:
    _logger.warning(
        'Setting "ACCRETE_USER_REGISTRATION_MAIL_FROM_NAME" missing.\n'
        'User Registration won\'t work. Set it or remove '
        'the app "accrete.contrib.user_registration".'
    )
