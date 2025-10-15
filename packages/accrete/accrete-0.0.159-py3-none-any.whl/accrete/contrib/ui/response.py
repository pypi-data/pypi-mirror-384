import re
import ast
import json
from dataclasses import dataclass

from django.core import paginator
from django.db.models import Model
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.utils.translation import gettext_lazy as _
from django.utils.functional import Promise
from accrete.contrib.ui import Filter


@dataclass(kw_only=True)
class WindowResponseConfig:

    display_header: bool = True

    def dict(self):
        return vars(self)


class Response:

    def __init__(self, *, template: str, context: dict):
        self.template = template
        self.context = context

    @staticmethod
    def add_trigger(response):
        pass

    def get_context(self):
        return self.context

    def render(self, request) -> str:
        return render_to_string(
            template_name=self.template, context=self.get_context(), request=request
        )

    def response(self, request, extra_content: str = None, replace_body: bool = False) -> HttpResponse:
        extra_content = extra_content or ''
        res = HttpResponse(content=(
            self.render(request)
            + render_to_string('ui/message.html', request=request)
            + extra_content
        ))
        self.add_trigger(res)
        if replace_body:
            res.headers['HX-Retarget'] = 'body'
            res.headers['HX-Reswap'] = 'innerHTML'
            res.headers['HX-Push-Url'] = request.path
        return res


class OobResponse(Response):

    oob_template = 'ui/oob.html'

    def __init__(self, *, template: str, context: dict, swap: str, tag: str = 'div', attrs: dict = None):
        super().__init__(template=self.oob_template, context=context)
        self.include_template = template
        self.swap = swap
        self.tag = tag
        self.attrs = attrs or {}

    def get_context(self):
        context = super().get_context()
        context.update({'oob': {
            'template': self.include_template,
            'swap': self.swap,
            'tag': self.tag,
            'attrs': self.attrs
        }})
        return context


class WindowResponse(Response):

    base_template = 'ui/layout.html'

    def __init__(
        self, *,
        title: str | Promise,
        context: dict = None,
        overview_template: str = None,
        header_template: str = None,
        panel_template: str = None,
        style_template: str = None,
        script_template: str = None,
        is_centered: bool = False,
        config: WindowResponseConfig = None
    ):
        super().__init__(template=self.base_template, context=context)
        self.title = title
        self.overview_template = overview_template
        self.header_template = header_template
        self.panel_template = panel_template
        self.panel_template = panel_template
        self.style_template = style_template
        self.script_template = script_template
        self.is_centered = is_centered
        self.config = config or WindowResponseConfig()

    def _has_panel(self):
        return bool(self.panel_template)

    def get_context(self):
        context = super().get_context()
        # TODO: move has_panel to config?
        if 'has_panel' not in context.keys():
            context.update(has_panel=self._has_panel())
        context.update({
            'title': self.title,
            'overview_template': self.overview_template,
            'header_template': self.header_template,
            'panel_template': self.panel_template,
            'style_template': self.style_template,
            'script_template': self.script_template,
            'is_centered': self.is_centered,
            'config': self.config.dict()
        })
        return context

    def response(self, request, extra_content: str = None, replace_body: bool = True) -> HttpResponse:
        return super().response(request, extra_content, replace_body)


class ListResponse(WindowResponse):

    def __init__(
        self, *,
        title: str,
        context: dict,
        list_entry_template: str = None,
        page: paginator.Page = None,
        ui_filter: Filter = None,
        endless_scroll: bool = True,
        header_template: str = None,
        panel_template: str = None,
        column_count: int = 1,
        column_height: str | None = '150px',
        overview_template: str = 'ui/list.html',
        detail_header_template: str = None,
        detail_data_template: str = None,
        detail_enabled: bool = True,
        config: WindowResponseConfig = None
    ):
        assert page is not None or ui_filter is not None, _(
            'Argument page or ui_filter must be supplied'
        )
        super().__init__(
            title=title,
            context=context,
            overview_template=overview_template,
            header_template=header_template,
            panel_template=panel_template,
            config=config
        )
        self.page = page or (ui_filter and ui_filter.get_page())
        self.list_entry_template = list_entry_template
        self.ui_filter = ui_filter
        self.endless_scroll = endless_scroll
        self.column_count = column_count
        self.column_height = column_height
        self.detail_header_template = detail_header_template
        self.detail_data_template = detail_data_template
        self.detail_enabled = detail_enabled

    def _has_panel(self):
        return bool(self.panel_template or self.ui_filter)

    def get_context(self):
        context = super().get_context()
        context.update({
            'list_entry_template': self.list_entry_template,
            'page': self.page,
            'ui_filter': self.ui_filter,
            'endless_scroll': self.endless_scroll,
            'column_count': self.column_count,
            'column_height': self.column_height,
            'detail_enabled': self.detail_enabled,
            'detail_header_template': self.detail_header_template,
            'detail_data_template': self.detail_data_template,
            'show_content_right': str(bool(
                self.detail_header_template or self.detail_data_template
            )).lower(),
        })
        return context

    def response(self, request, extra_content: str = None, replace_body: bool = False) -> HttpResponse:
        return super().response(request, extra_content, replace_body)


class ListEntryResponse(Response):

    base_template = 'ui/list_update.html'

    def __init__(
        self, *,
        instance: Model,
        list_entry_template: str,
        context: dict = None,
        page: paginator.Page = None,
        is_new: bool = False,
        column_count: int = 1,
        column_height: str = '150px',
    ):
        super().__init__(template=self.base_template, context=context or {})
        self.instance = instance
        self.instance.refresh_from_db()
        self.list_entry_template = list_entry_template
        self.page = page
        self.is_new = is_new
        self.column_count = column_count
        self.column_height = column_height

    def get_context(self):
        context = super().get_context()
        context.update({
            'instance': self.instance,
            'list_entry_template': self.list_entry_template,
            'is_new': self.is_new,
            'column_count': self.column_count,
            'column_height': self.column_height
        })
        return context

    def render(self, request) -> str:
        res = super().render(request)
        if self.page:
            pagination_update = OobResponse(
                template='ui/layout.html#pagination',
                swap='innerHTML:#pagination',
                context=dict(page=self.page)
            ).render(request)
            res += pagination_update
        return res


class TableResponse(WindowResponse):

    def __init__(
        self, *,
        title: str | Promise,
        context: dict,
        fields: list[str],
        instance_label: str | Promise | None = None,
        footer: dict = None,
        page: paginator.Page = None,
        ui_filter: Filter = None,
        endless_scroll: bool = True,
        header_template: str = None,
        panel_template: str = None,
        overview_template: str = 'ui/table.html',
        detail_header_template: str = None,
        detail_data_template: str = None,
        detail_enabled: bool = True,
        config: WindowResponseConfig = None
    ):
        assert page is not None or ui_filter is not None, _(
            'Argument page or ui_filter must be supplied'
        )
        super().__init__(
            title=title,
            context=context,
            overview_template=overview_template,
            header_template=header_template,
            panel_template=panel_template,
            config=config
        )
        self.instance_label = instance_label
        self.fields = fields
        self.footer = footer
        self.page = page or (ui_filter and ui_filter.get_page())
        self.ui_filter = ui_filter
        self.endless_scroll = endless_scroll
        self.detail_header_template = detail_header_template
        self.detail_data_template = detail_data_template
        self.detail_enabled = detail_enabled

    def _has_panel(self):
        return bool(self.panel_template or self.ui_filter)

    def get_context(self):
        context = super().get_context()
        context.update({
            'page': self.page,
            'ui_filter': self.ui_filter,
            'endless_scroll': self.endless_scroll,
            'fields': self.fields,
            'instance_label': self.instance_label,
            'footer': self.footer,
            'detail_header_template': self.detail_header_template,
            'detail_data_template': self.detail_data_template,
            'detail_enabled': self.detail_enabled,
            'show_content_right': str(bool(
                self.detail_header_template or self.detail_data_template
            )).lower()
        })
        return context

    def response(self, request, extra_content: str = None, replace_body: bool = False) -> HttpResponse:
        return super().response(request, extra_content, replace_body)


class TableRowResponse(Response):

    base_template = 'ui/table_row_update.html'

    def __init__(
        self, *,
        instance: Model,
        fields: list[str],
        instance_label: str | Promise | None = None,
        footer: dict = None,
        page: paginator.Page = None,
    ):
        super().__init__(template=self.base_template, context={})
        self.instance = instance
        self.instance.refresh_from_db()
        self.fields = fields
        self.instance_label = instance_label
        self.footer = footer
        self.page = page

    def get_context(self):
        context = super().get_context()
        context.update({
            'instance': self.instance,
            'fields': self.fields,
            'instance_label': self.instance_label,
            'footer': self.footer,
            'page': self.page
        })
        return context

    def render(self, request) -> str:
        res = super().render(request)
        if self.page:
            pagination_update = OobResponse(
                template='ui/layout.html#pagination',
                swap='innerHTML:#pagination',
                context=dict(page=self.page)
            ).render(request)
            res += pagination_update
        return res


class DetailResponse(Response):

    base_template = 'ui/detail.html'

    def __init__(
        self, *,
        context: dict,
        header_template: str = None,
        data_template: str = None
    ):
        super().__init__(template=self.base_template, context=context)
        self.header_template = header_template
        self.data_template = data_template
        self.context.update()

    @staticmethod
    def add_trigger(response):
        add_trigger(response, 'activate-detail')

    def get_context(self):
        context = super().get_context()
        context.update({
            'detail_header_template': self.header_template,
            'detail_data_template': self.data_template
        })
        return context


class ModalResponse(Response):

    def __init__(
        self, *,
        modal_id: str,
        template: str,
        context: dict,
        title: str | Promise = None,
        is_update: bool = False,
        is_blocking: bool = False,
        modal_width: str = None

    ):
        super().__init__(template=template, context=context)
        self.modal_id = modal_id
        self.title = title
        self.is_update = is_update
        self.is_blocking = is_blocking
        self.modal_width = modal_width

    def get_context(self):
        context = super().get_context()
        context.update({
            'title': self.title,
            'modal_id': re.sub(r'[^A-Za-z-]+', '', self.modal_id).strip('-'),
            'is_update': self.is_update,
            'is_blocking': self.is_blocking,
            'modal_width': self.modal_width
        })
        return context


@dataclass
class ClientTrigger:

    trigger: dict | str
    header: str = 'HX-Trigger'


class TriggerResponse:

    def __init__(self, trigger: list[ClientTrigger]):
        self.trigger = trigger

    def response(self):
        res = HttpResponse()
        res.headers['HX-Reswap'] = 'none'
        for trigger in self.trigger:
            add_trigger(res, trigger.trigger, trigger.header)
        return res


def search_select_response(queryset) -> HttpResponse:
    return HttpResponse(render_to_string(
        'ui/widgets/model_search_select_options.html',
        {'options': queryset}
    ))


def message_response(request, persistent: bool = False):
    return HttpResponse(content=(render_to_string(
        'ui/message.html', context={'persistent': persistent}, request=request
    )))


def add_trigger(
    response: HttpResponse,
    trigger: dict | str,
    header: str = 'HX-Trigger'
) -> HttpResponse:
    if isinstance(trigger, str):
        trigger = {trigger: ''}
    res_trigger = response.headers.get(header)
    if not res_trigger:
        response.headers[header] = json.dumps(trigger)
        return response
    try:
        res_trigger = ast.literal_eval(response.headers.get(header, '{}'))
    except SyntaxError:
        res_trigger = {response.headers[header]: ''}
    res_trigger.update(trigger)
    response.headers[header] = json.dumps(res_trigger)
    return response


def update(request, ui_responses: list[Response], trigger: list[ClientTrigger] = None) -> HttpResponse:
    response = HttpResponse()
    content = ''
    for res in ui_responses:
        content += res.render(request)
        res.add_trigger(response)
    content += render_to_string('ui/message.html', request=request)
    response.content = content
    for t in trigger or []:
        add_trigger(response, t.trigger, t.header)
    return response


def redirect_response(url: str, reload: bool = True):
    res = HttpResponse()
    header = 'HX-Redirect' if reload else 'HX-Location'
    res[header] = url
    return res
