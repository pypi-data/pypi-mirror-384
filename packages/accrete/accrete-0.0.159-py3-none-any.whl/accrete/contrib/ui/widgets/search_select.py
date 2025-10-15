from uuid import uuid4
from django.forms import widgets
from django.shortcuts import resolve_url


class ModelSearchSelect(widgets.NumberInput):
    template_name = 'ui/widgets/model_search_select.html'
    option_template_name = 'ui/widgets/model_search_select_options.html'
    input_type = 'number'

    def __init__(
        self,
        search_url: str,
        search_kwargs: dict = None,
        search_parameter: str = 'search',
        limit: int | None = 5,
        hx_trigger_on_change: bool = False,
        choices=()
    ):
        super().__init__()
        self.search_url = search_url
        self.search_kwargs = search_kwargs or {}
        self.search_parameter = search_parameter
        self.limit = limit
        self.hx_trigger_on_change = hx_trigger_on_change  # trigger htmx request on change
        self.choices = choices

    def get_context(self, name, value, attrs):
        qs = self.choices.queryset
        if self.limit:
            qs = qs[:self.limit]
        uuid = str(uuid4())

        context = {
            "widget": {
                "name": name,
                "is_hidden": self.is_hidden,
                "required": self.is_required,
                "value": self.format_value(value or ''),
                'value_display': self.value_display(value),
                "attrs": self.build_attrs(self.attrs, attrs),
                "template_name": self.template_name,
                'search_url': resolve_url(self.search_url, **self.search_kwargs),
                'search_parameter': self.search_parameter,
                'hx_trigger_on_change': self.hx_trigger_on_change,
                'uuid': uuid
            },
            'options': qs
        }
        return context

    def format_value(self, value):
        res = super().format_value(value)
        return res or ''

    def value_display(self, value):
        if value is None:
            return ''
        try:
            value = int(value)
        except ValueError:
            return ''
        return str(self.choices.queryset.get(pk=value))


class ModelSearchSelectMulti(widgets.SelectMultiple):
    template_name = 'ui/widgets/model_search_select_multi.html'
    option_template_name = 'ui/widgets/model_search_select_options.html'
    input_type = 'number'

    def __init__(
        self,
        search_url: str,
        search_kwargs: dict = None,
        search_parameter: str = 'search',
        limit: int | None = 5,
        hx_trigger_on_change: bool = False,
        choices=()
    ):
        super().__init__()
        self.search_url = search_url
        self.search_kwargs = search_kwargs or {}
        self.search_parameter = search_parameter
        self.limit = limit
        self.hx_trigger_on_change = hx_trigger_on_change  # trigger 'change' event on the actual input field
        self.choices = choices

    def get_context(self, name, value, attrs):
        qs = self.choices.queryset
        if self.limit:
            qs = qs[:self.limit]
        uuid = uuid4()

        context = {
            "widget": {
                "name": name,
                "is_hidden": self.is_hidden,
                "required": self.is_required,
                "value": self.format_value(value),
                "attrs": self.build_attrs(self.attrs, attrs),
                "template_name": self.template_name,
                'search_url': resolve_url(self.search_url, **self.search_kwargs),
                'search_parameter': self.search_parameter,
                'hx_trigger_on_change': self.hx_trigger_on_change,
                'uuid': uuid
            },
            'options': qs,
            'selected': self.choices.queryset.filter(pk__in=value) if value else qs.none()
        }
        return context
