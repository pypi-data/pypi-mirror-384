from django.core.exceptions import ValidationError
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from accrete.tenant import get_tenant
from accrete.managers import TenantManager, MemberManager, AccessGroupManager
from accrete.fields import TranslatedCharField, TranslatedTextField


class TenantModel(models.Model):

    class Meta:
        abstract = True

    tenant = models.ForeignKey(
        verbose_name=_('Tenant'),
        to='accrete.Tenant',
        on_delete=models.CASCADE
    )

    objects = TenantManager()

    def save(
        self,
        *args,
        force_insert=False,
        force_update=False,
        using=None,
        update_fields=None
    ):
        tenant = get_tenant()
        if self.pk and tenant and self.tenant != tenant:
            raise ValueError('Current tenant differs from tenant of the record!')
        if self.pk and not self.tenant and not tenant:
            raise ValueError(
                'Tenant not provided! '
                'Use accrete.tenant.set_tenant() '
                'or set the tenant explicitly on the instance.'
            )
        if tenant:
            self.tenant = tenant
        super().save(
            force_insert=force_insert,
            force_update=force_update,
            using=using,
            update_fields=update_fields
        )

    @staticmethod
    def exclude_from_filter():
        return ['tenant']


class Tenant(models.Model):

    class Meta:
        verbose_name = _('Tenant')
        verbose_name_plural = _('Tenants')
        ordering = ['-is_active', 'name']
        db_table = 'accrete_tenant'

    name = models.CharField(
        verbose_name=_('Name'),
        max_length=255
    )

    is_active = models.BooleanField(
        verbose_name=_('Active'),
        default=True
    )

    access_groups = models.ManyToManyField(
        to='accrete.AccessGroup',
        through='accrete.TenantAccessGroupRel',
        through_fields=('tenant', 'access_group'),
        blank=True
    )

    def __str__(self):
        return self.name


class Member(models.Model):

    class Meta:
        verbose_name = _('Member')
        verbose_name_plural = _('Members')
        ordering = ['tenant', 'user']
        db_table = 'accrete_member'

    user = models.ForeignKey(
        to=settings.AUTH_USER_MODEL,
        related_name='memberships',
        on_delete=models.CASCADE
    )

    tenant = models.ForeignKey(
        to='accrete.Tenant',
        related_name='members',
        on_delete=models.CASCADE
    )

    is_active = models.BooleanField(
        verbose_name=_('Active'),
        default=True
    )

    access_groups = models.ManyToManyField(
        to='accrete.AccessGroup',
        through='accrete.MemberAccessGroupRel',
        through_fields=('member', 'access_group'),
        blank=True
    )

    objects = MemberManager()

    def __str__(self):
        return f'{self.user}'


class AccessGroup(models.Model):

    class Meta:
        verbose_name = _('Access Group')
        verbose_name_plural = _('Access Groups')
        ordering = ['name']
        db_table = 'accrete_access_group'
        constraints = [
            models.UniqueConstraint(
                name='unique_code',
                fields=['code']
            )
        ]

    objects = AccessGroupManager()

    name = TranslatedCharField(
        verbose_name=_('Name')
    )

    description = TranslatedTextField(
        verbose_name=_('Description'),
        null=True,
        blank=True
    )

    code = models.CharField(
        verbose_name=_('Code'),
        max_length=100
    )

    apply_on = models.CharField(
        verbose_name=_('Apply On'),
        max_length=10,
        choices=[
            ('tenant', _('Tenant')),
            ('member', _('Member'))
        ],
        default='tenant'
    )

    def __str__(self):
        return f'{self.name} ({self.get_apply_on_display()})'


class MemberAccessGroupRel(models.Model):

    class Meta:
        verbose_name = _('Member Access Group Relation')
        verbose_name_plural = _('Member Access Group Relations')
        ordering = ['member']
        db_table = 'accrete_member_access_group_rel'
        constraints = [
            models.UniqueConstraint(
                name='unique_member_per_group',
                fields=['member', 'access_group']
            )
        ]

    member = models.ForeignKey(
        to='accrete.Member',
        on_delete=models.CASCADE
    )

    access_group = models.ForeignKey(
        to='accrete.AccessGroup',
        on_delete=models.CASCADE
    )

    def __str__(self):
        return f'{self.member} - {self.access_group}'

    def clean(self):
        if self.access_group.apply_on != 'member':
            raise ValidationError(_('Access Group must apply on members'))


class TenantAccessGroupRel(models.Model):

    class Meta:
        verbose_name = _('Tenant Access Group Relation')
        verbose_name_plural = _('Tenant Access Groups Relations')
        ordering = ['tenant']
        db_table = 'accrete_tenant_access_group_rel'
        constraints = [
            models.UniqueConstraint(
                name='unique_tenant_per_group',
                fields=['tenant', 'access_group']
            )
        ]

    tenant = models.ForeignKey(
        to='accrete.Tenant',
        on_delete=models.CASCADE
    )

    access_group = models.ForeignKey(
        to='accrete.AccessGroup',
        on_delete=models.CASCADE
    )

    def __str__(self):
        return f'{self.tenant} - {self.access_group}'

    def clean(self):
        if self.access_group.apply_on != 'tenant':
            raise ValidationError(_('Access Group must apply on tenants'))
