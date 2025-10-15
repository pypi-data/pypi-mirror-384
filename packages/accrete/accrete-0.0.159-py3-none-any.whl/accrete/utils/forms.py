import re
import logging
from uuid import uuid4
from typing import Type, Any
from dataclasses import dataclass, field
from django.db import transaction
from django.forms import BaseFormSet, Form, ModelForm

_logger = logging.getLogger(__name__)


@dataclass
class FormResult:

    form: Form | ModelForm
    is_saved: bool = False
    save_error: str | None = None
    save_error_id: str | None = None
    res: Any = None  # return value of form.save()
    inline_formsets: list = field(default_factory=list)

    def __getattr__(self, item):
        return getattr(self.form, item)

    def __getitem__(self, item):
        return self.form.__getitem__(item)


def save_form(
    form: Form | ModelForm,
    *,
    commit: bool = True,
    check_changed: bool = False,
    reraise: bool = False
) -> FormResult:
    if not hasattr(form, 'save'):
        raise AttributeError('Form must have method "save" implemented.')
    result = FormResult(form=form)
    changed = not check_changed or form.has_changed()
    try:
        if form.is_valid():
            if changed:
                with transaction.atomic():
                    result.res = form.save(commit=commit)
            result.is_saved = True
    except Exception as e:
        result.save_error = repr(e)
        error_id = str(uuid4())[:8]
        _logger.exception(f'{error_id}: {e}')
        result.save_error_id = error_id
        if reraise:
            raise e
    return result


def save_forms(form, inline_formsets: list = None, commit=True, reraise: bool = False) -> FormResult:

    def handle_error(error):
        result.save_error = repr(error)
        error_id = str(uuid4())[:8]
        _logger.exception(f'{error_id}: {error}')
        result.save_error_id = error_id

    if not hasattr(form, 'save'):
        raise AttributeError('Form must have method "save" implemented.')

    result = FormResult(form=form)
    result.inline_forms = inline_formsets

    try:
        form.is_valid()
        inlines_valid = all([
            inline_formset.is_valid() for inline_formset in result.inline_formsets
        ])
    except Exception as e:
        handle_error(e)
        if reraise:
            raise e
        return result

    if not form.is_valid() or not inlines_valid:
        return result

    try:
        with transaction.atomic():
            result.res = form.save(commit=commit)
            for inline_formset in result.inline_formsets:
                inline_formset.save(commit=commit)
    except Exception as e:
        handle_error(e)
        if reraise:
            raise e
        return result

    result.is_saved = True
    return result


def inline_vals_from_post(post: dict, prefix: str) -> list[dict]:
    post_keys = set(re.findall(f'{prefix}-[0-9]+', ', '.join(post.keys())))
    initial_data = {
        post_key: {}
        for post_key in post_keys if not post.get(f'{post_key}-DELETE')
    }
    for key, val in post.items():
        post_key = '-'.join(key.split('-')[:-1])
        if post_key not in initial_data:
            continue
        field_name = key.split('-')[-1]
        initial_data[post_key].update({field_name: val})
    return [val for val in initial_data.values()]


def extend_formset(formset_class, post: dict, data: list[dict]|dict, **formset_kwargs) -> Type[BaseFormSet]:
    formset = formset_class(post, **formset_kwargs)
    if not formset.is_valid():
        return formset
    form_data = post.copy()
    if isinstance(data, dict):
        data = [data]
    prefix = formset_kwargs.get('prefix', 'form')
    total = int(form_data[f'{prefix}-TOTAL_FORMS']) - 1
    for item in data:
        total += 1
        form_data.update({f'{prefix}-{total}-{key}': value for key, value in item.items()})
    form_data[f'{prefix}-TOTAL_FORMS'] = total + 1
    formset = formset_class(form_data, **formset_kwargs)
    for form in formset:
        form._errors = {}
    return formset
