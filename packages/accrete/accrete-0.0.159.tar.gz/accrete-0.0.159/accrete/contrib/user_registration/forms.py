from uuid import uuid4
import logging

from django.contrib.auth import get_user_model
from django.utils.http import urlsafe_base64_encode
from django.core.validators import validate_email
from django.utils.translation import gettext_lazy as _
from django import forms

from .models import UserConfirmationToken

_logger = logging.getLogger(__name__)
User = get_user_model()


class UserRegistrationForm(forms.Form):
    email = forms.EmailField(
        label='E-Mail', widget=forms.EmailInput
    )

    password1 = forms.CharField(
        label=_('Password'),
        widget=forms.PasswordInput,
        max_length=128
    )

    password2 = forms.CharField(
        label=_('Confirm Password'),
        widget=forms.PasswordInput,
        max_length=128
    )

    def clean_password1(self):
        pw = self.cleaned_data['password1']
        if len(pw) < 1:
            raise forms.ValidationError(_(
                'Password must be at least 8 characters long!'
            ))
        return pw

    def clean(self):
        super().clean()
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        msg = _("Passwords don't match!")

        if password1 and password2 and password1 != password2:
            self.add_error('password2', msg)

        return self.cleaned_data

    def clean_email(self):
        email = self.cleaned_data.get('email', '').lower()
        validate_email(email)

        if User.objects.filter(email=email):
            raise forms.ValidationError(
                _('This email address is already bound to an account.')
            )

        return email

    def save(self):
        user = User(
            email=self.cleaned_data.get('email'),
            is_staff=False,
            is_superuser=False,
            is_active=False
        )
        user.set_password(self.cleaned_data["password1"])
        user.save()
        _logger.info(f'Registering user {user}')

        token = urlsafe_base64_encode(str(uuid4()).encode())
        user_confirmation_token = UserConfirmationToken(
            user=user,
            token=token
        )
        user_confirmation_token.save()

        return user


class ResendConfirmationMailForm(forms.Form):
    email = forms.EmailField(
        label='E-Mail', widget=forms.EmailInput
    )

    def clean_email(self):
        email = self.cleaned_data['email']
        validate_email(email)
        return email


class ConfirmRegistrationForm(forms.Form):
    token = forms.CharField()

    def clean_token(self):
        token = self.cleaned_data['token']
        user_token = self.get_user_token(token)
        if not token or not user_token:
            raise forms.ValidationError(_(
                'Invalid token supplied.'
            ))

        if user_token.user.is_active:
            raise forms.ValidationError(_(
                'User already activated'
            ))

        return token

    @staticmethod
    def get_user_token(token):
        return UserConfirmationToken.objects.filter(token=token).first()

    def save(self):
        user_token = self.get_user_token(self.cleaned_data['token'])
        user_token.user.is_active = True
        user_token.user.save()
        user_token.delete()
        _logger.info(f'Confirmed User Registration for {user_token.user}')
