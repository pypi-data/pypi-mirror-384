import json
import logging
import datetime
from decimal import Decimal

from django.db.models import QuerySet, Q
from django.http.request import QueryDict
from django.db.models.fields import Field
from django.template.loader import render_to_string
from django.utils.translation import gettext_lazy as _
from django.utils.safestring import mark_safe
from django.apps import apps
from django.core import paginator
from accrete.utils.models import get_related_model, get_related_field
from accrete.utils import page_from_querystring, filter_from_querystring

_logger = logging.getLogger(__name__)


class Filter:

    LABEL_EXACT = _('Equals')
    LABEL_EXACT_NOT = _('Equals Not')
    LABEL_ICONTAINS = _('Contains')
    LABEL_ICONTAINS_NOT = _('Contains Not')
    LABEL_GTE = _('Greater or Equal')
    LABEL_LTE = _('Less or Equal')
    LABEL_TRUE = _('True')
    LABEL_FALSE = _('False')
    LABEL_SET = _('Is Set')
    LABEL_NOT_SET = _('Is Not Set')
    LABEL_AND = _('And')
    LABEL_OR = _('Or')
    LABEL_XOR = _('Not Or')

    DATE_FORMAT = '%Y-%m-%d'

    TYPES_INTEGER = [
        'AutoField', 'BigAutoField', 'IntegerField', 'PositiveSmallIntegerField'
    ]
    TYPES_NUMBER = ['DecimalField', 'FloatField']
    TYPES_CHAR = ['CharField', 'TextField']
    TYPES_BOOL = ['BooleanField']
    TYPES_DATETIME = ['DateTimeField']
    TYPES_DATE = ['DateField']
    TYPES_TIME = ['TimeField']

    def __init__(
        self,
        model,
        query_dict: QueryDict,
        default_lookup: str = None,
        query: Q = None,
        select_related: list[str] = None,
        prefetch_related: list[str] = None
    ):
        self.model = model
        self.query_dict = query_dict
        self.model_name = f'{self.model._meta.app_label}.{self.model._meta.model_name}'
        self.query = query or Q()
        self.select_related = select_related
        self.prefetch_related = prefetch_related
        seen_models = query_dict.get('models', '').split(',')
        self.seen_models = [
            model for model in seen_models
            if model and model != self.model_name
        ] + [self.model_name]
        self.default_lookup = default_lookup
        self.exclude = []
        if hasattr(self.model, 'exclude_from_filter'):
            self.exclude.extend(self.model.exclude_from_filter())

    def get_page(
        self, select_related: list = None, prefetch_related: list = None,
        query: Q = None
    ) -> paginator.Page:
        return page_from_querystring(
            self.model,
            self.query_dict,
            select_related=select_related or self.select_related,
            prefetch_related=prefetch_related or self.prefetch_related,
            query=query or self.query
        )

    def get_queryset(self) -> QuerySet:
        return filter_from_querystring(self.model, self.query_dict).filter(self.query)

    def query_params(self):
        fields = filter(
            lambda x: x.name not in self.exclude,
            self.model._meta.get_fields()
        )
        params = []
        path = self.query_dict.get('path', '')
        for field in fields:
            field_params = self._get_field_params(field)
            if not field.is_relation or field_params['model_name'] not in self.seen_models:
                params.append(self._get_field_params(field))
        has_previous = len(self.seen_models) > 1
        ctx = dict(
            params=sorted(params, key=lambda x: x['label'].lower()),
            model_name=self.model_name,
            seen_models=','.join(self.seen_models),
            verbose_model_name=self.model._meta.verbose_name,
            has_previous=has_previous,
        )
        if has_previous:
            previous_model_name = self.seen_models[-2]
            previous_path = '__'.join(path.split('__')[:-1])
            ctx.update(
                previous_model_name=previous_model_name,
                previous_seen_models=','.join(
                    self.seen_models[:-1] if has_previous else []
                ),
                previous_verbose_model_name=apps.get_model(
                    *previous_model_name.split('.')
                )._meta.verbose_name,
                previous_path=previous_path
            )
        return render_to_string('ui/filter/query_params.html', ctx)

    def query_input(self, lookup: str = None):
        lookup = lookup or self.default_lookup
        if not lookup:
            ctx = {
                'verbose_lookup': str(_('Select an attribute')),
                'query_dict': self.query_dict,
                'model_name': self.model_name
            }
            return render_to_string('ui/filter/query_input.html', ctx)
        prefix = lookup.startswith('~') and '~' or ''
        lookup = lookup.removeprefix('~')
        lookup_parts = lookup.split('__')
        lookup_operator = lookup_parts[-1]
        rel_path = '__'.join(lookup_parts[:-2])
        model, names = get_related_model(self.model, rel_path)
        field = model._meta.get_field(lookup_parts[-2])
        input_params = self._get_input_params(field, lookup_operator)
        ctx = {
            'verbose_lookup': ' > '.join(self._get_query_tag_lhs(prefix + lookup)),
            'field': field,
            'lookup': prefix + lookup,
            'input': input_params,
            'lookup_operator': lookup_operator,
            'query_dict': self.query_dict,
            'model_name': self.model_name
        }
        return render_to_string('ui/filter/query_input.html', ctx)

    def query_tags(self, query: list | dict = None, operator: str = None):
        if not query:
            query = json.loads(self.query_dict.get('q', '[]'))
        if isinstance(query, dict):
            query = [query]
        operator = operator or '&'
        html = '<div class="query-group-container">'
        html += render_to_string(
            'ui/filter/query_operator.html', {'operator': operator}
        )
        html += (
            '<div class="query-group" '
            'x-sort="applyQuery();" x-sort:group="query" '
            'x-sort:config="{preventOnFilter: false}">'
        )
        for idx, item in enumerate(query):
            if isinstance(item, str):
                continue
            operator = '&'
            if idx > 0 and isinstance(query[idx - 1], str):
                operator = query[idx - 1]
            if isinstance(item, list):
                html += self.query_tags(item, operator)
            if isinstance(item, dict):
                item_ctx = self._get_query_tag_context(item, operator)
                html += render_to_string('ui/filter/query_tags.html', item_ctx)
        html += '</div></div>'
        return mark_safe(html)

    def _get_input_params(self, field: Field, lookup_operator: str):
        field_type = field.get_internal_type()
        params = {
            'field_type': field_type,
            'data_type': self._internal_type_to_data_type(field_type, lookup_operator)
        }
        if lookup_operator == 'isnull':
            params.update(
                input_type='select',
                choices=[('false', str(_('True'))), ('true', str(_('False')))],
                data_type='bool'
            )
            return params
        if field_type in self.TYPES_BOOL:
            params.update(
                input_type='select',
                choices=[('true', str(_('True'))), ('false', str(_('False')))],
                data_type='bool'
            )
            return params
        elif field_type in self.TYPES_INTEGER:
            if field.choices:
                params.update(input_type='select', choices=field.choices)
            else:
                params.update(input_type='number', step=1)
        elif field_type in self.TYPES_NUMBER:
            step = (
                hasattr(field, 'decimal_places')
                and self._cast_decimal_places_to_step(field.decimal_places)
                or 1
            )
            params.update(input_type='number', step=step)
        elif field_type in self.TYPES_CHAR:
            if field.choices:
                params.update(input_type='select', choices=field.choices)
            else:
                params.update(input_type='text')
        elif field_type in self.TYPES_DATETIME:
            params.update(input_type='datetime-local', format=self.DATE_FORMAT)
        elif field_type in self.TYPES_DATE:
            params.update(input_type='date', format=self.DATE_FORMAT)
        elif field_type in self.TYPES_TIME:
            params.update(input_type='time')
        return params

    def _internal_type_to_data_type(self, internal_type, lookup: str):
        if lookup == 'isnull' or internal_type in self.TYPES_BOOL:
            return 'bool'
        if internal_type in self.TYPES_INTEGER + self.TYPES_NUMBER:
            return 'number'
        return 'text'

    def _get_query_tag_context(self, data: dict, operator: str):
        ctx = {'tags': []}
        first_operator = operator
        operator = '&'
        for key, value in data.items():

            field_path = key.split('__')
            field = get_related_field(
                self.model, '__'.join(field_path[:-1]).removeprefix('~')
            )
            lookup = field_path[-1]
            internal_type = field.get_internal_type()
            data_type = self._internal_type_to_data_type(internal_type, lookup)
            ctx['tags'].append({
                'lhs': self._get_query_tag_lhs(key),
                'rhs': self._get_query_tag_rhs(value, internal_type, lookup),
                'lookup': key,
                'value': value,
                'operator': operator,
                'data_type': data_type,
                'model_name': self.model_name
            })
        if ctx['tags']:
            ctx['tags'][0]['operator'] = first_operator
        return ctx

    def _get_query_tag_lhs(self, lookup: str):
        prefix = lookup.startswith('~') and '~' or ''
        lookup = lookup.removeprefix('~')
        parts = lookup.split('__')
        assert len(parts) >= 2
        related_parts = parts[:-2]
        rel_model, names = get_related_model(
            self.model, '__'.join(related_parts)
        )
        try:
            names.extend([
                str(rel_model._meta.get_field(parts[-2]).verbose_name),
                str(self._get_lookup_label(f'{prefix}{parts[-1]}'))
            ])
        except AttributeError:
            names.extend([
                str(rel_model._meta.get_field(parts[-2]).field.verbose_name),
                str(self._get_lookup_label(f'{prefix}{parts[-1]}'))
            ])
        return names[1:]

    def _get_query_tag_rhs(self, value, internal_type, lookup):
        if lookup == 'isnull':
            return not value
        if internal_type in self.TYPES_DATE:
            return datetime.date.fromisoformat(value)
        if internal_type in self.TYPES_DATETIME:
            return datetime.datetime.fromisoformat(value)
        if internal_type in self.TYPES_NUMBER:
            return Decimal(value)
        return value

    def _get_lookup_label(self, lookup: str):
        labels = {
            'exact': self.LABEL_EXACT,
            '~exact': self.LABEL_EXACT_NOT,
            'icontains': self.LABEL_ICONTAINS,
            '~icontains': self.LABEL_ICONTAINS_NOT,
            'gte': self.LABEL_GTE,
            'lte': self.LABEL_LTE,
            'isnull': self.LABEL_SET,
            '~isnull': self.LABEL_NOT_SET
        }
        return str(labels[lookup])

    def _get_field_params(self, field):
        path = self.query_dict.get('path', '')
        label = ''
        name = field.name
        if path:
            field_path = f'{path}__{name}'
        else:
            field_path = name
        field_type = field.get_internal_type()
        if field.concrete or not field.is_relation:
            label = str(field.verbose_name)
        if field.is_relation:
            choices = None
            step = None
            model = ''
            if field_type in ['ForeignKey', 'OneToOneField']:
                model = (
                    f'{field.related_model._meta.app_label}.'
                    f'{field.related_model._meta.model_name}'
                )
                if not field.concrete:
                    label = str(
                        field.related_model._meta.verbose_name_plural
                    )
            elif field_type == 'ManyToManyField':
                model = (
                    f'{field.remote_field.model._meta.app_label}.'
                    f'{field.remote_field.model._meta.model_name}'
                )
                if not field.concrete:
                    label = (
                        f'{field.remote_field.model._meta.verbose_name} / '
                        f'{field.remote_field.verbose_name}'
                    )
        else:
            step = (
                hasattr(field, 'decimal_places')
                and self._cast_decimal_places_to_step(field.decimal_places)
                or 1
            )
            choices = field.choices or None
            model = self.model_name
        return {
            'field': field,
            'name': name,
            'field_path': field_path,
            'label': label,
            'type': field_type,
            'param_type': '',
            'choices': choices,
            'null': field.null,
            'step': step,
            'is_relation': field.is_relation,
            'model_name': model,
        }

    @staticmethod
    def _cast_decimal_places_to_step(decimal_places):
        if not decimal_places or decimal_places < 1:
            return '1'
        zero_count = decimal_places - 1
        return f'0.{"0" * zero_count}1'
