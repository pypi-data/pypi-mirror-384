import logging
from celery import shared_task, current_app
from celery.schedules import crontab
from django.core import mail
from django.db import transaction
from django.utils.html import strip_tags
from .models import SystemMail

_logger = logging.getLogger(__name__)


@current_app.on_after_finalize.connect
def setup_periodic_tasks(sender, **kwargs):
    sender.add_periodic_task(
        crontab(hour='*', minute='*/5'),
        run_mail_queue.s()
    )


@shared_task()
def run_mail_queue():
    with transaction.atomic():
        _logger.info('Starting System Mail Queue')
        mails_to_send = SystemMail.objects.filter(
            sent=False).select_for_update()
        for email in mails_to_send:
            _logger.info(f'Sending mail: {email}')
            try:
                msg = strip_tags(email.body)
                mail.send_mail(
                    email.subject, msg, email.from_name,
                    email.to_addr.split(','), html_message=email.body
                )
            except Exception as e:
                error_str = str(e)
                _logger.error(f'Failed to send system mail\n{error_str}')
                email.error = error_str
                email.save()
            else:
                email.sent = True
                email.error = None
                email.save()
