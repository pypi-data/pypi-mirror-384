import logging

from django.db import models

from accrete.tenant import get_member, get_tenant
from accrete.utils.log import log_time
from .models import Log, LogConfig
from . import helper, queries, config

_logger = logging.getLogger(__name__)


@log_time
def create_log(sender, **kwargs):
    if (
        sender._meta.object_name == 'Migration'
        and not config.ACCRETE_LOG_RUN_IN_MIGRATION
    ):
        return

    def _create_log():
        member = get_member()
        user = member and member.user or None
        object_id = instance.id
        log_rows = queries.current_log_state(model, object_id)
        log_state, log_info = helper.log_state_to_dict(log_rows)
        instance_state = helper.get_instance_state(instance)
        diff = dict(log_state.items() ^ instance_state.items())
        logs_to_create = []
        for field, value in instance_state.items():
            if field not in diff.keys():
                continue
            value_type = helper.internal_type_to_log_type(instance._meta.get_field(field))
            if value_type is None:
                continue
            if value is None:
                new_value = None
            else:
                new_value = str(value)
            log = Log(
                model=model,
                field=field,
                object_id=instance.id,
                old_value_type=log_info.get(field, {}).get('new_value_type', ''),
                old_value=log_state.get(field),
                new_value_type=helper.internal_type_to_log_type(instance._meta.get_field(field)),
                new_value=new_value,
                user=user,
                tenant=get_tenant()
            )
            logs_to_create.append(log)
        Log.objects.bulk_create(logs_to_create)

    instance: models.Model = kwargs.get('instance')
    model = f'{instance._meta.app_label}.{instance._meta.model_name}'
    log_config = LogConfig.objects.filter(model=model).first()
    if not log_config:
        return
    try:
        _create_log()
    except Exception as e:
        _logger.exception(e)
        if not log_config.ignore_errors:
            raise e
