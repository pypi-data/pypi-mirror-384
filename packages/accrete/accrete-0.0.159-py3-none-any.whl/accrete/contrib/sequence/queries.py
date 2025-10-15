from django.db import transaction
from django.db.models import F

from accrete.tenant import get_tenant
from .models import Sequence


def get_nextval(name: str, create_if_none:bool = True) -> int:
    tenant = get_tenant()
    with transaction.atomic():
        seq = Sequence.objects.filter(
            tenant=tenant, name=name
        ).select_for_update().first()

        if seq is None and not create_if_none:
            raise ValueError(f'Sequence "{name}" does not exist.')
        elif seq is None:
            seq = Sequence(name=name, tenant=tenant)
            seq.save()

        nextval = seq.nextval
        seq.nextval = F('nextval') + seq.step
        seq.save()

    return nextval
