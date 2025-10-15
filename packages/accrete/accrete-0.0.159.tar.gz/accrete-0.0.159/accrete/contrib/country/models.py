from django.db import models
from django.utils.translation import gettext_lazy as _
from accrete.fields import TranslatedCharField


class Country(models.Model):

    class Meta:
        verbose_name = _('Country')
        verbose_name_plural = _('Countries')
        db_table = 'accrete_country'
        ordering = ['-order_priority', 'name']

    name = TranslatedCharField(
        verbose_name=_('Name')
    )

    iso_code_a2 = models.CharField(
        verbose_name=_('ISO Code Alpha 2'),
        max_length=2
    )

    iso_code_a3 = models.CharField(
        verbose_name=_('ISO Code Alpha 3'),
        max_length=3
    )

    vat_prefix = models.CharField(
        verbose_name=_('VAT ID Prefix'),
        max_length=3,
        null=True,
        blank=True
    )

    order_priority = models.IntegerField(
        verbose_name=_('Order Priority'),
        default=0
    )

    def __str__(self):
        return self.name
