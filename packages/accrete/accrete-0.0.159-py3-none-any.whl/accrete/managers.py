from django.db import models
from accrete.tenant import get_tenant


class TenantManager(models.Manager):

    def get_queryset(self):
        queryset = super().get_queryset()
        tenant = get_tenant()
        if tenant:
            queryset = queryset.filter(tenant=tenant)
        return queryset

    def bulk_create(
            self,
            objs,
            batch_size=None,
            ignore_conflicts=False,
            update_conflicts=False,
            update_fields=None,
            unique_fields=None,
    ):
        tenant = get_tenant()
        if tenant is None and any(obj.tenant_id in (False, None) for obj in objs):
            raise ValueError(
                'Tenant must be set for all objects when calling '
                'bulk_create without an active tenant set.'
            )
        list(map(
            lambda x: setattr(x, 'tenant_id', tenant.pk),
            filter(lambda o: o.tenant_id is None, objs)
        ))
        if tenant is not None and any(obj.tenant_id != tenant.pk for obj in objs):
            raise ValueError(
                'Objects must have set the active Tenant when calling '
                'bulk_create while a tenant is active.'
            )
        return super().bulk_create(
            objs, batch_size=batch_size, ignore_conflicts=ignore_conflicts,
            update_conflicts=update_conflicts, update_fields=update_fields,
            unique_fields=unique_fields
        )


class MemberManager(TenantManager):

    def get_queryset(self):
        queryset = super().get_queryset().select_related('tenant', 'user')
        return queryset


class AccessGroupManager(models.Manager):

    def tenant_groups(self):
        return self.get_queryset().filter(apply_on='tenant')

    def member_groups(self):
        return self.get_queryset().filter(apply_on='member')
