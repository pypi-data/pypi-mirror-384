from django.db import models
from django.utils.translation import gettext_lazy as _

from accrete.models import TenantModel


class Sequence(TenantModel):

    class Meta:
        db_table = 'accrete_sequence'
        constraints = [
            models.UniqueConstraint(
                name='unique_name_per_tenant',
                fields=['name', 'tenant']
            ),
            models.UniqueConstraint(
                name='unique_val_per_name_tenant',
                fields=['name', 'tenant', 'nextval']
            )
        ]

    name = models.CharField(
        verbose_name=_('Name'),
        max_length=255,
    )

    nextval = models.PositiveBigIntegerField(
        verbose_name=_('Next Value'),
        default=1
    )

    step = models.PositiveIntegerField(
        verbose_name=_('Step'),
        default=1
    )

    def __str__(self):
        return self.name
