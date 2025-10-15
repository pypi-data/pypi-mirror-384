import json
from django.db import connection
from django.db.models import Model, Field
from django.forms import model_to_dict as mtd

from accrete.fields import TranslatedCharField, TranslatedTextField


def get_related_model(model: type[Model], rel_path: str) -> tuple[Model, list[str]]:
    names = []
    related_model = model
    for part in rel_path.split('__'):
        names.append(str(related_model._meta.verbose_name))
        try:
            next_model = related_model._meta.fields_map[part].related_model
            related_model = next_model
        except (AttributeError, KeyError):
            try:
                next_model = getattr(related_model, part).field.related_model
                if next_model is not None:
                    related_model = next_model
            except AttributeError:
                break
    names.append(str(related_model._meta.verbose_name))
    return related_model, names


def get_related_field(model: type[Model], field_path: str) -> Field:
    parts = field_path.split('__')
    rel_path = '__'.join(parts[:-1])
    rel_model, _ = get_related_model(model, rel_path)
    return rel_model._meta.get_field(parts[-1])


def translated_db_value(instance: Model, field: str) -> dict:
    if not instance.pk:
        return dict()
    with connection.cursor() as cr:
        query = """SELECT %s FROM %s WHERE id = %s""" % (
            field,
            instance._meta.db_table,
            instance.pk
        )
        cr.execute(query)
        row = cr.fetchone()
        row = row and row[0]
        db_value = row and json.loads(row) or dict()
    return db_value


def model_to_dict(instance, fields=None, exclude=None, translated=True):
    """
    Extends django.forms.model_to_dict with the option to get the
    translation dict instead of the translated string for the active language
    """
    data = mtd(instance, fields=fields, exclude=exclude)
    if translated:
        return data
    updates = {}
    for f, v in data.items():
        if isinstance(instance._meta.get_field(f), (TranslatedCharField, TranslatedTextField)):
            updates.update({f: translated_db_value(instance, f)})
    data.update(updates)
    return data
