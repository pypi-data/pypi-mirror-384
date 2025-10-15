import logging
from django.conf import settings

_logger = logging.getLogger(__name__)

ACCRETE_TENANT_QUICK_SWITCH_URL = getattr(
    settings, 'ACCRETE_TENANT_QUICK_SWITCH_URL',
    False
)
