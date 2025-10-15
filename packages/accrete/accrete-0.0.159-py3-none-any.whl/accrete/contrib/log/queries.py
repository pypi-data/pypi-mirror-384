from django.db.models.query import RawQuerySet

from .models import Log
from accrete.tenant import get_tenant


def current_log_state(model: str, object_id: int) -> RawQuerySet:
    tenant = get_tenant()
    tenant_id = tenant and tenant.id or None
    logs = Log.objects.raw("""
        SELECT
            log_value.id,
            log_value.model,
            log_value.field,
            log_value.object_id,
            log_value.log_date,
            log_value.old_value_type,
            log_value.new_value_type,
            log_value.old_value,
            log_value.new_value
        FROM (
            SELECT model, field, object_id, MAX(log_date) AS log_date
            FROM accrete_log
            WHERE
                model = %s AND
                object_id = %s AND
                tenant_id = %s
            GROUP BY model, field, object_id
        ) log_result
        JOIN accrete_log log_value ON
            log_value.model = log_result.model AND
            log_value.field = log_result.field AND
            log_value.object_id = log_result.object_id AND
            log_result.log_date = log_value.log_date;
    """, [model, object_id, tenant_id])
    return logs
