import logging
import re
from datetime import datetime, date, timedelta

from django.contrib.auth import get_user_model
from django.shortcuts import resolve_url
from django.utils.translation import gettext_lazy as _
from django import template
from django.db.models import (
    Manager, DecimalField, IntegerField, FloatField, Model,
    ManyToManyRel, ManyToManyField
)
from django.apps import apps
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe
from django.forms import widgets
from accrete.contrib.ui.models import Theme
from accrete.tenant import get_tenant, unscoped
from accrete.models import Tenant, Member
from accrete.contrib.ui import config

_logger = logging.getLogger(__name__)
register = template.Library()
User = get_user_model()


@register.simple_tag(name='combine_templates')
def combine_templates(template_name, request=None):
    html = ''
    for app in apps.app_configs.keys():
        try:
            html += render_to_string(
                f'{app}/{template_name}',
                request=request
            )
        except template.TemplateDoesNotExist:
            continue
    return mark_safe(html)


@register.filter(name='related_obj_url')
def related_obj_url(param: object, value: str):
    attr = getattr(param, value, False)
    if attr and hasattr(attr, 'get_absolute_url'):
        return attr.get_absolute_url()
    return '#'


@register.filter(name='get_attr')
def get_attr_from_string(param: object, value: str):

    def return_save(attr):
        if isinstance(attr, Manager) and hasattr(attr, 'related_model'):
            return attr.related_model
        if attr is None:
            return None
        if isinstance(attr, str):
            return attr
        return attr

    try:
        attribute = getattr(param, value, False)
    except (AttributeError,):
        _logger.warning(f'Object {param} has no attribute {value}')
        attribute = None
    return return_save(attribute)


@register.filter(name='has_attr')
def has_attr(param: object, value:str):
    return hasattr(param, value)


@register.filter(name='get_item')
def get_item(param, value):
    return param[value]


@register.filter(name='get_model')
def get_model(instance):
    return instance._meta.model


@register.filter(name='verbose_field_name')
def verbose_field_name(param: object, value: str):
    if not param:
        return ''
    if isinstance(param, Model):
        field = param._meta.get_field(value)
        if isinstance(field, ManyToManyRel):
            name = field.related_model._meta.verbose_name_plural
        else:
            name = param._meta.get_field(value).verbose_name
    else:
        field = getattr(param.model, value).field
        if isinstance(field, ManyToManyField):
            name = field.model._meta.verbose_name_plural
        else:
            name = getattr(param.model, value).field.verbose_name
        
    return name


@register.filter(name='table_display')
def table_display(param: object, value: str):
    field = getattr(param, value)
    if isinstance(field, Manager):
        return mark_safe(f"""
            <span>            
                <div class="tags">
                    {''.join(['<span class="tag">{}</span>'.format(o) for o in field.all()])}
                </div>
            </span>
        """)
    return get_attr_from_string(param, value)


@register.filter(name='table_alignment')
def table_alignment(param, value):
    if isinstance(param, str):
        return 'left'
    if isinstance(param, Model):
        field = param._meta.get_field(value)
    else:
        field = getattr(param.model, value).field
    if isinstance(field, (DecimalField, IntegerField, FloatField)):
        return 'right'
    return 'left'


@register.filter(name='message_class')
def message_class(message):
    if message.level == 25:
        return 'is-success'
    if message.level == 30:
        return 'is-warning'
    if message.level == 40:
        return 'is-danger'
    return ''


@register.filter(name='timedelta_cast')
def timedelta_cast(td: timedelta, code: str) -> str | None:
    if not isinstance(td, timedelta):
        return None
    codes = ['days', 'hours', 'minutes', 'seconds', 'microseconds']
    if code not in codes:
        return None
    return str(getattr(td, code))


@register.filter(name='weekday')
def datetime_to_weekday(dt: datetime|date|str, default=None) -> str:
    if dt is None:
        return default
    if isinstance(dt, str):
        dt = datetime.strptime(dt, '%Y-%m-%d')
    mapping = {
        1: _('Mon'),
        2: _('Tue'),
        3: _('Wed'),
        4: _('Thu'),
        5: _('Fri'),
        6: _('Sat'),
        7: _('Sun')
    }
    return mapping[dt.isoweekday()]


@register.filter(name='xrefsave')
def x_ref_save(param: str):
    return re.sub(r'[^A-Za-z]+','', param)


@register.filter(name='wrap_form_field')
def wrap_form_field(field, icon=None):
    if isinstance(field.field.widget, widgets.Textarea):
        html = render_to_string(
            'ui/templatetags/field.html#textarea',
            {'field': field, 'icon': None}
        )
        return mark_safe(html)
    if isinstance(field.field.widget, widgets.CheckboxInput):
        html = render_to_string(
            'ui/templatetags/field.html#form_checkbox',
            {'field': field, 'icon': None}
        )
        return mark_safe(html)
    html = render_to_string(
        'ui/templatetags/field.html#form_field',
        {'field': field, 'icon': icon}
    )
    return mark_safe(html)


@register.filter(name='wrap_model_field')
def wrap_model_field(instance, field_name):
    field = instance._meta.get_field(field_name)
    if field.choices:
        value = getattr(instance, f'get_{field_name}_display')()
    else:
        value = getattr(instance, field_name)
    html = render_to_string(
        'ui/templatetags/field.html#model_field', {
            'label': field.help_text or field.verbose_name,
            'value': value
        })
    return mark_safe(html)


@register.filter(name='wrap_model_state')
def wrap_model_state(instance, field_name):
    field = instance._meta.get_field(field_name)
    # get choices, handle groups


@register.filter(name='default_if_falsy')
def default_if_falsy(value, default):
    if bool(value):
        return value
    return default


@register.simple_tag(name='custom_theme')
def custom_theme(user: User) -> str:
    if user.is_anonymous:
        return ''
    tenant = get_tenant()
    tenant_theme = Theme.objects.filter(
        tenant=tenant, tenant__isnull=False
    ).first()
    if tenant_theme and tenant_theme.force_tenant_theme:
        return mark_safe(tenant_theme.theme_markup)
    if user.theme == 'custom':
        theme = Theme.objects.filter(user=user).first()
        return theme and mark_safe(theme.theme_markup) or ''
    if user.theme == 'preset' and tenant_theme:
        return mark_safe(tenant_theme.theme_markup)
    return ''


@register.simple_tag(name='base_theme')
def base_theme(user: User) -> str:
    if user.is_anonymous:
        return 'light'
    tenant = get_tenant()
    tenant_theme = Theme.objects.filter(
        tenant=tenant, tenant__isnull=False
    ).first()
    if tenant_theme and tenant_theme.force_tenant_theme:
        return tenant_theme.base_theme
    if user.theme == 'custom':
        theme = Theme.objects.filter(user=user).first()
        return theme and theme.base_theme or 'light'
    if user.theme == 'preset' and tenant_theme:
        return tenant_theme.base_theme
    return user.theme


@register.simple_tag(name='tenant_quick_switch')
def tenant_quick_switch(user: User):
    templ = 'ui/templatetags/tenant_quick_switch.html'
    tenant = get_tenant()
    with unscoped():
        tenants = Tenant.objects.filter(
            members__in=Member.objects.filter(user=user)
        )
        if tenant:
            tenants = tenants.exclude(pk=tenant.pk)
    switch_url = getattr(config, 'ACCRETE_TENANT_QUICK_SWITCH_URL')
    if switch_url:
        switch_url = resolve_url(switch_url)
    return mark_safe(render_to_string(
        templ, context={
            'tenant': tenant,
            'tenants': tenants,
            'switch_url': switch_url
        }
    ))
