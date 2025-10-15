import json
from django import forms
from django.db import connection
from django.db.models import JSONField
from django.core import checks
from django.utils.translation import get_language, gettext_lazy as _
from django.utils.text import capfirst
from django.conf import settings


class TranslatedCharField(JSONField):

    description = _("A JSON object to store translated strings")
    default_language = settings.LANGUAGE_CODE

    def check(self, **kwargs):
        errors = super().check(**kwargs)
        errors.extend(self._check_choices())
        return errors

    def _check_choices(self):
        errors = []
        if self.choices is not None:
            errors.append(
                checks.Error(
                    "%s does not support Choices." % type(self).__name__,
                    obj=self.model,
                    id="fields.E180",
                )
            )
        return errors

    def pre_save(self, model_instance, add):
        if not model_instance.pk:
            old_val = dict()
        else:
            with connection.cursor() as cr:
                query = """SELECT %s FROM %s WHERE id = %s""" % (
                    self.attname,
                    model_instance._meta.db_table,
                    model_instance.pk
                )
                cr.execute(query)
                row = cr.fetchone()
                row = row and row[0]
                old_val = row and json.loads(row) or dict()
        language = get_language()
        new_val = getattr(model_instance, self.attname)
        if new_val in [None, False, '']:
            return {self.default_language: ''}
        if isinstance(new_val, dict):
            old_val.update(new_val)
            # new_val = new_val.get(language, '')
        else:
            old_val.update({language: new_val})
        if language != self.default_language and not old_val.get(self.default_language):
            old_val.update({self.default_language: new_val})
        return old_val

    def from_db_value(self, value, expression, connection):
        value = super().from_db_value(value, expression, connection)
        language = get_language()
        if value is None:
            return None
        if not isinstance(value, dict):
            value = dict()
        char_val = value.get(language)
        if not char_val:
            char_val = value.get(self.default_language, None)
        return char_val

    def to_python(self, value):
        if value is None:
            return None
        if isinstance(value, str):
            return value
        language = get_language()
        char_value = ''
        if isinstance(value, dict):
            char_value = value.get(language)
            if not char_value:
                char_value = value.get(self.default_language, '')
        return char_value

    def formfield(self, form_class=None, choices_form_class=None, **kwargs):
        defaults = {
            "required": not self.blank,
            "label": capfirst(self.verbose_name),
            "help_text": self.help_text,
        }
        if self.has_default():
            if callable(self.default):
                defaults["initial"] = self.default
                defaults["show_hidden_initial"] = True
            else:
                defaults["initial"] = self.get_default()
        if self.choices is not None:
            # Fields with choices get special treatment.
            include_blank = self.blank or not (
                self.has_default() or "initial" in kwargs
            )
            defaults["choices"] = self.get_choices(include_blank=include_blank)
            defaults["coerce"] = self.to_python
            if self.null:
                defaults["empty_value"] = None
            if choices_form_class is not None:
                form_class = choices_form_class
            else:
                form_class = forms.TypedChoiceField
            # Many of the subclass-specific formfield arguments (min_value,
            # max_value) don't apply for choice fields, so be sure to only pass
            # the values that TypedChoiceField will understand.
            for k in list(kwargs):
                if k not in (
                    "coerce",
                    "empty_value",
                    "choices",
                    "required",
                    "widget",
                    "label",
                    "initial",
                    "help_text",
                    "error_messages",
                    "show_hidden_initial",
                    "disabled",
                ):
                    del kwargs[k]
        defaults.update(kwargs)
        if form_class is None:
            form_class = forms.CharField
        return form_class(**defaults)


class TranslatedTextField(TranslatedCharField):

    def formfield(self, form_class=None, choices_form_class=None, **kwargs):
        if form_class is None:
            form_class = forms.CharField
            kwargs.update(widget=forms.Textarea)
        return super().formfield(
            form_class=form_class,
            choices_form_class=choices_form_class,
            **kwargs
        )
