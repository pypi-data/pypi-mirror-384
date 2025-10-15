import logging
from django import forms
from accrete.tenant import get_tenant

_logger = logging.getLogger(__name__)


class TenantForm(forms.Form):

    def __init__(self, *args, **kwargs):
        self.tenant = get_tenant()
        super().__init__(*args, **kwargs)
        fields_to_filter = filter(
            lambda x:
            hasattr(x, 'queryset') and hasattr(x.queryset.model, 'tenant'),
            self.fields.values()
        )
        for field in fields_to_filter:
            field.queryset = field.queryset.filter(tenant=self.tenant)


class TenantModelForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        self.tenant = get_tenant()
        super().__init__(*args, **kwargs)
        fields_to_filter = filter(
            lambda x:
            hasattr(x, 'queryset') and hasattr(x.queryset.model, 'tenant'),
            self.fields.values()
        )
        for field in fields_to_filter:
            field.queryset = field.queryset.filter(tenant=self.tenant)

    def save(self, commit=True):
        super().save(commit=False)
        if not self.instance.pk or not self.instance.tenant:
            self.instance.tenant = self.tenant

        if commit:
            self.instance.save()
            self.save_m2m()
        return self.instance
