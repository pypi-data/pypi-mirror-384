from django import forms
from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from . models import Theme


class ThemeForm(forms.ModelForm):

    class Meta:
        model = Theme
        fields = [
            'user',
            'tenant',
            'base_theme',
            'color_primary',
            'color_success',
            'color_link',
            'color_warning',
            'color_danger'
        ]
        widgets = {
            'color_primary': forms.widgets.TextInput(attrs={'type': 'color', 'autocomplete': 'off'}),
            'color_success': forms.widgets.TextInput(attrs={'type': 'color', 'autocomplete': 'off'}),
            'color_link': forms.widgets.TextInput(attrs={'type': 'color', 'autocomplete': 'off'}),
            'color_warning': forms.widgets.TextInput(attrs={'type': 'color', 'autocomplete': 'off'}),
            'color_danger': forms.widgets.TextInput(attrs={'type': 'color', 'autocomplete': 'off'}),
            'user': forms.widgets.HiddenInput(),
            'tenant': forms.widgets.HiddenInput()
        }

    def _clean_color(self, hex_color: str):
        if not hex_color.startswith('#'):
            hex_color = f'#{hex_color}'
        if len(hex_color) != 7:
            raise forms.ValidationError(_(
                'Color must be of length 7 and including the starting "#"'
            ))
        return hex_color

    def clean_color_primary(self):
        color = self._clean_color(self.cleaned_data.get('color_primary'))
        return color

    def clean_color_success(self):
        color = self._clean_color(self.cleaned_data.get('color_success'))
        return color

    def clean_color_link(self):
        color = self._clean_color(self.cleaned_data.get('color_link'))
        return color

    def clean_color_warning(self):
        color = self._clean_color(self.cleaned_data.get('color_warning'))
        return color

    def clean_color_danger(self):
        color = self._clean_color(self.cleaned_data.get('color_danger'))
        return color
