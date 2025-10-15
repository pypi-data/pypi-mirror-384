import logging
from django.conf import settings

_logger = logging.getLogger(__name__)

ACCRETE_TENANT_NOT_SET_URL = getattr(
    settings, 'ACCRETE_TENANT_NOT_SET_URL',
    False
)

ACCRETE_GROUP_NOT_SET_URL = getattr(
    settings, 'ACCRETE_GROUP_NOT_SET_URL',
    False
)

if not ACCRETE_TENANT_NOT_SET_URL:
    _logger.warning(
        'Setting ACCRETE_TENANT_NOT_SET_URL missing.'
    )
