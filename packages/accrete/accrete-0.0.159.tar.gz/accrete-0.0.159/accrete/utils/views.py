import logging
import json
import operator
from typing import Callable

from django.core import paginator
from django.db.models import Model, Q, QuerySet
from django.template.loader import render_to_string, TemplateDoesNotExist
from django.http import HttpResponseNotAllowed
from accrete.utils.models import get_related_model

_logger = logging.getLogger(__name__)

QUERYSTRING_KEY_MAP = {
    'querystring': 'q',
    'order': 'order',
    'paginate_by': 'paginate_by',
    'page': 'page'
}


def page_from_querystring(
    model: type[Model], query_dict: dict, key_map: dict = None,
    select_related: list = None, prefetch_related: list = None,
    query: Q = None
) -> paginator.Page:

    key_map = key_map or QUERYSTRING_KEY_MAP
    query = query or Q()
    queryset = filter_from_querystring(
        model, query_dict, key_map
    ).filter(
        query
    ).select_related(
        *select_related or []
    ).prefetch_related(
        *prefetch_related or []
    )
    return get_page(
        queryset,
        cast_param(query_dict, key_map.get('paginate_by'), int, 40),
        cast_param(query_dict, key_map.get('page'), int, 1)
    )


def get_page(queryset: QuerySet, paginate_by: int, page_number: int) -> paginator.Page:
    pages = paginator.Paginator(queryset, per_page=paginate_by)
    return pages.page(
        page_number <= pages.num_pages and page_number or pages.num_pages
    )


def filter_from_querystring(
        model: type[Model], query_dict: dict, key_map: dict = None
) -> QuerySet:

    key_map = key_map or QUERYSTRING_KEY_MAP
    querystring = query_dict.get(key_map['querystring'], '[]')
    order = query_dict.get(key_map['order']) or model._meta.ordering

    return model.objects.filter(
        parse_querystring(model, querystring)
    ).order_by(*order).distinct()


def parse_querystring(model: type[Model], query_string: str) -> Q:
    """
    param: query_string: JSON serializable string
    Parses
    [{"term": value}, "&", [{"term": value}, "|", {"~term": value}]]
    to
    Q(term=value) & (Q(term=value) | ~Q(term=value))
    """

    def get_expression(term: str, value) -> Q:
        invert = False
        if term.startswith('~'):
            invert = True
            term = term[1:]

        parts = term.split('__')
        if len(parts) == 1:
            expression = Q(**{term: value})
            return ~expression if invert else expression

        rel_path = '__'.join(parts[:-2])
        related_model, x = get_related_model(model, rel_path)
        expression = Q(**{term: value})
        return ~expression if invert else expression

    def parse_query_block(sub_item) -> Q:
        op = ops['&']
        parsed_query = Q()
        for item in sub_item:
            if isinstance(item, list):
                parsed_query = op(parsed_query, parse_query_block(item))
                op = ops['&']
            elif isinstance(item, dict):
                dict_query = Q()
                for term, value in item.items():
                    dict_query = ops['&'](dict_query, get_expression(term, value))
                parsed_query = op(parsed_query, dict_query)
            elif isinstance(item, str):
                if item not in '&|^':
                    raise ValueError(
                        f'Invalid operator in querystring: {item}.'
                        f'Operator must be one of &, |, ^'
                    )
                op = ops[item]
            else:
                raise ValueError(
                    f'Unsupported item in querystring: {item}.'
                    f'Item must be an instance of list, dict or str'
                )
        return parsed_query

    query_data = json.loads(query_string.strip('?&='))
    if isinstance(query_data, dict):
        query_data = [query_data]

    ops = {'&': operator.and_, '|': operator.or_, '^': operator.xor}
    query = parse_query_block(query_data)
    return query


def cast_param(params: dict, param: str, cast_to: Callable, default):
    if param not in params:
        return default
    try:
        return cast_to(params.get(param, default))
    except Exception as e:
        _logger.exception(e)
        return default


def method_not_allowed(method: str, allowed: list[str]) -> HttpResponseNotAllowed | None:
    return None if method in allowed else HttpResponseNotAllowed(allowed)


def render_templates(
    templates: list[str | tuple[str, dict]],
    context: dict = None,
    request=None
) -> str:
    context = {} if context is None else context
    content = ''
    for template in templates:
        if isinstance(template, tuple):
            template_name, template_context = template
        else:
            template_name, template_context = template, context
        try:
            content += render_to_string(template_name, template_context, request)
        except TemplateDoesNotExist as e:
            _logger.warning(repr(e))
        except Exception as e:
            _logger.exception(repr(e))
            raise e
    return content
