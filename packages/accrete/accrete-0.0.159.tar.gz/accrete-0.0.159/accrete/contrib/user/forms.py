from django import forms
from django.conf import settings
from django.core.validators import validate_email
from django.utils.translation import gettext_lazy as _
from django.forms import ModelForm, fields, ValidationError, PasswordInput, EmailInput
from .models import User


class UserForm(ModelForm):

    language_code = fields.ChoiceField(
        label=_('Language'),
        choices=settings.LANGUAGES,
        required=True
    )

    class Meta:
        model = User
        fields = [
            'username',
            'first_name',
            'last_name',
            'theme'
        ]

        widgets = {
            'theme': forms.RadioSelect(
                attrs={'autocomplete': 'off'}
            )
        }

    def save(self, commit=True):
        super().save(commit=False)
        self.instance.language_code = self.cleaned_data['language_code']
        if commit:
            self.instance.save()
            self.save_m2m()


class ChangePasswordForm(ModelForm):

    old_password = fields.CharField(
        label=_('Old password'),
        widget=PasswordInput(render_value=True),
        max_length=128,
    )

    new_password = fields.CharField(
        label=_('New password'),
        widget=PasswordInput(render_value=True),
        max_length=128
    )

    new_password_confirm = fields.CharField(
        label=_('New password confirmation'),
        widget=PasswordInput(render_value=True),
        max_length=128
    )

    class Meta:
        model = User
        fields = []

    def clean_old_password(self):
        old_password = self.cleaned_data['old_password']
        if not self.instance.check_password(old_password):
            raise ValidationError(_(
                'Password Validation failed'
            ))
        return old_password

    def clean(self):
        super().clean()
        new_password = self.cleaned_data.get('new_password')
        new_password_confirm = self.cleaned_data.get('new_password_confirm')
        if new_password != new_password_confirm:
            raise ValidationError(
                _('New password and confirmation did not match.')
            )
        return self.cleaned_data

    def save(self, commit=True):
        user = self.instance
        user.set_password(self.cleaned_data['new_password'])
        user.save()


class ChangeEmailForm(ModelForm):

    email = fields.EmailField(
        label=_('New Email Address'),
        widget=EmailInput(),
    )

    password = fields.CharField(
        label=_('Password'),
        widget=PasswordInput()
    )

    class Meta:
        model = User
        fields = []

    def clean_email(self):
        email = self.cleaned_data.get('email', '').lower()
        validate_email(email)
        if User.objects.filter(email=email):
            raise ValidationError(
                _('This email address is already bound to an account.')
            )
        return email

    def clean_password(self):
        password = self.cleaned_data.get('password')
        if not self.instance.check_password(password):
            raise ValidationError(_(
                'Password incorrect'
            ))
        return password

    def save(self, commit=True):
        self.instance.email = self.cleaned_data['email']
        self.instance.save()
