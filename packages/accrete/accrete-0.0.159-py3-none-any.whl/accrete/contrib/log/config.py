from django.conf import settings

ACCRETE_LOG_RUN_IN_MIGRATION = getattr(
    settings, 'ACCRETE_LOG_RUN_IN_MIGRATION',
    False
)
