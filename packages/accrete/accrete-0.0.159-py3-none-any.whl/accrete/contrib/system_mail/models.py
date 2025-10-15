from django.db import models
from django.utils.translation import gettext_lazy as _


class SystemMail(models.Model):
    class Meta:
        db_table = 'system_mail'

    from_name = models.CharField(
        verbose_name=_('From'),
        max_length=255
    )

    to_addr = models.TextField(
        verbose_name=_('To'),
        help_text=_('E-Mail addresses, comma separated')
    )

    subject = models.CharField(
        verbose_name=_('Subject'),
        max_length=255,
        default=''
    )

    body = models.TextField(
        verbose_name=_('Mail Body'),
        default=''
    )

    sent = models.BooleanField(
        verbose_name=_('E-Mail sent'),
        default=False
    )

    error = models.TextField(
        verbose_name=_('Errors'),
        null=True,
        blank=True
    )

    def __str__(self):
        return f'{self.to_addr}: {self.subject}'
