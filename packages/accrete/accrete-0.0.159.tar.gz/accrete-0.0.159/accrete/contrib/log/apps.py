from django.apps import AppConfig
from django.db.models.signals import post_save


class LogConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accrete.contrib.log'

    def ready(self):
        from . import signals
        post_save.connect(
            signals.create_log, weak=False, dispatch_uid="accrete.contrib.log"
        )
