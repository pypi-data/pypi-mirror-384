from decimal import Decimal
from datetime import date, datetime

from django.conf import settings
from django.db.models.functions import Lower
from django.utils.translation import gettext_lazy as _
from django.db import models
import logging
_logger = logging.getLogger(__name__)


class Log(models.Model):

    class Meta:
        verbose_name = _('Log')
        verbose_name_plural = _('Logs')
        db_table = 'accrete_log'
        indexes = [
            models.Index(fields=['model', 'object_id', 'tenant_id'])
        ]
        constraints = [
            models.UniqueConstraint(
                name='unique_group_fields',
                fields=('model', 'field', 'object_id', 'log_date')
            )
        ]

    tenant = models.ForeignKey(
        verbose_name=_('Tenant'),
        to='accrete.Tenant',
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    model = models.CharField(
        verbose_name=_('Model'),
        max_length=255,
        help_text='Combination of app label and model name seperated by a dot'
    )

    field = models.CharField(
        verbose_name=_('Field'),
        max_length=255
    )

    object_id = models.BigIntegerField(
        verbose_name='Object ID'
    )

    log_date = models.DateTimeField(
        verbose_name=_('Date'),
        auto_now_add=True
    )

    old_value_type = models.CharField(
        verbose_name=_('Old Value Type'),
        choices=[
            ('fk', 'Foreign Key'),
            ('int', 'Integer'),
            ('float', 'Float'),
            ('decimal', 'Decimal'),
            ('bool', 'Boolean'),
            ('str', 'String'),
            ('date', 'Date'),
            ('datetime', 'Date Time'),
            ('json', 'JSON')
        ],
        max_length=100,
    )

    new_value_type = models.CharField(
        verbose_name=_('New Value Type'),
        choices=[
            ('fk', 'Foreign Key'),
            ('int', 'Integer'),
            ('float', 'Float'),
            ('decimal', 'Decimal'),
            ('bool', 'Boolean'),
            ('str', 'String'),
            ('date', 'Date'),
            ('datetime', 'Date Time'),
            ('json', 'JSON')
        ],
        max_length=100
    )

    old_value = models.TextField(
        verbose_name=_('Old Value'),
        null=True,
        blank=True
    )

    new_value = models.TextField(
        verbose_name=_('New Value'),
        null=True,
        blank=True
    )

    user = models.ForeignKey(
        to=settings.AUTH_USER_MODEL,
        related_name='logs',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    def __str__(self):
        return f'{self.model}.{self.field},{self.object_id}'

    def cast_value(self):
        if self.new_value is None:
            return None
        if self.new_value_type == 'fk':
            return self.cast_fk()
        if self.new_value_type == 'int':
            return self.cast_int()
        if self.new_value_type == 'float':
            return self.cast_float()
        if self.new_value_type == 'decimal':
            return self.cast_decimal()
        if self.new_value_type == 'bool':
            return self.cast_bool()
        if self.new_value_type == 'str':
            return self.cast_str()
        if self.new_value_type == 'date':
            return self.cast_date()
        if self.new_value_type == 'datetime':
            return self.cast_date_time()

    def cast_fk(self):
        return self.cast_int()

    def cast_int(self):
        if self.new_value == '':
            return None
        return int(self.new_value)

    def cast_float(self):
        if self.new_value == '':
            return 0.0
        return float(self.new_value)

    def cast_decimal(self):
        if self.new_value == '':
            return Decimal(0)
        return Decimal(self.new_value)

    def cast_bool(self):
        return self.new_value == 'True'

    def cast_str(self):
        return self.new_value

    def cast_date(self):
        if self.new_value == '':
            return None
        return date.fromisoformat(str(self.new_value))

    def cast_date_time(self):
        if self.new_value == '':
            return None
        return datetime.fromisoformat(self.new_value)


class LogConfig(models.Model):

    class Meta:
        verbose_name = _('Log Configuration')
        verbose_name_plural = _('Log Configs')
        db_table = 'accrete_log_config'
        ordering = [Lower('model')]
        indexes = [
            models.Index(fields=['model'])
        ]
        constraints = [
            models.UniqueConstraint(
                name='unique_model',
                fields=('model',)
            )
        ]

    model = models.CharField(
        verbose_name=_('Model'),
        max_length=255,
        help_text=_('Combination of app label and model name seperated by a dot')
    )

    ignore_errors = models.BooleanField(
        verbose_name=_('Ignore Errors'),
        default=False,
        help_text=_('If set, exceptions during log creation will be ignored')
    )

    exclude_fields = models.BooleanField(
        verbose_name=_('Exclude Fields'),
        default=False,
        help_text=_(
            'If set, Log Configuration Fields will be excluded from logging. '
            'Otherwise only configured fields will be logged.'
        )
    )

    def __str__(self):
        return self.model


class LogConfigField(models.Model):

    class Meta:
        verbose_name = _('Log Configuration Field')
        verbose_name_plural = _('Log Configuration Fields')
        db_table = 'accrete_log_config_field'
        ordering = [Lower('field_name')]
        indexes = [
            models.Index(fields=['log_config'])
        ]
        constraints = [
            models.UniqueConstraint(
                name='unique_config_field_name',
                fields=('log_config', 'field_name')
            )
        ]

    log_config = models.ForeignKey(
        verbose_name=_('Log Configuration'),
        to='log.LogConfig',
        related_name='fields',
        on_delete=models.CASCADE
    )

    field_name = models.CharField(
        verbose_name=_('Field Name'),
        max_length=255,
        help_text=_('Name of the field to log')
    )

    def __str__(self):
        return f'{self.log_config}.{self.field_name}'
