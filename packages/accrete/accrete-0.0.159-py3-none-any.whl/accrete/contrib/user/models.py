from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.contrib.auth.models import (
    AbstractBaseUser,
    PermissionsMixin
)
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.contrib.auth.models import BaseUserManager
from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.shortcuts import resolve_url

from accrete.models import Tenant

LANGUAGE_DISPLAY = {
    lang[0]: lang[1]
    for lang in settings.LANGUAGES
}


def validate_member_login(login: str) -> None:
    if '@' in login:
        raise ValidationError(_(
            'Login must not be an E-Mail address, use the field email instead'
        ))
    message = _(
        'Login must consist of username and domain seperated by a colon(":")'
    )
    if ':' not in login:
        raise ValidationError(message)
    member_login, tenant_login = login.split(':', 1)
    if not member_login or not tenant_login:
        raise ValidationError(message)


def default_language_code():
    return settings.LANGUAGE_CODE


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, password, email=None, login=None, username=None, **extra_fields):
        if not email and not login:
            raise ValueError('The email or login must be set')
        if not username and login:
            username = login
        elif not username and email:
            username = email
        user = self.model(**extra_fields)
        if email:
            user.email = self.normalize_email(email)
        if login:
            user.login = self.model.normalize_username(login)
        if username:
            user.username = self.model.normalize_username(username)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, password, email=None, login=None, username=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        extra_fields.setdefault('is_active', False)
        return self._create_user(password, email, login, username, **extra_fields)

    def create_superuser(self, password, email, username=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(password, email, username, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):

    class Meta:
        db_table = 'accrete_user'
        verbose_name = _('User')
        verbose_name_plural = _('Users')
        constraints = [
            models.CheckConstraint(
                condition=Q(email__isnull=False) | Q(login__isnull=False),
                name='email_or_login_set',
                violation_error_message='E-Mail or Login must be set'
            ),
            models.CheckConstraint(
                condition=Q(is_managed=True, login__isnull=False) | Q(is_managed=False),
                name='managed_login',
                violation_error_message='Managed users must have a login'
            )
        ]

    username_validator = UnicodeUsernameValidator()
    login_validator = validate_member_login

    username = models.CharField(
        verbose_name=_('Username'),
        max_length=150,
        help_text=_(
            '150 characters or fewer.'
            'Letters, digits and @/./+/-/_ only.'
        ),
        blank=True,
        null=True,
        validators=[username_validator],
    )

    first_name = models.CharField(
        verbose_name=_('First Name'),
        max_length=150,
        blank=True,
        null=True
    )

    last_name = models.CharField(
        verbose_name=_('Last Name'),
        max_length=150,
        blank=True,
        null=True
    )

    email = models.EmailField(
        verbose_name=_('Email Address'),
        unique=True,
        null=True
    )

    login = models.CharField(
        verbose_name=_('Login'),
        max_length=254,
        validators=[login_validator],
        unique=True,
        null=True
    )

    is_staff = models.BooleanField(
        verbose_name=_('Staff Status'),
        default=False,
        help_text=_(
            'Designates whether the user can log into the admin site.'
        ),
    )

    is_active = models.BooleanField(
        verbose_name=_('Active'),
        default=True,
        help_text=_(
            'Designates whether this user should be treated as active.\n'
            'Unselect this instead of deleting accounts.'
        ),
    )

    is_managed = models.BooleanField(
        verbose_name=_('Is Managed'),
        default=False,
        help_text=_('User with restricted functionality.')
    )

    date_joined = models.DateTimeField(
        verbose_name=_('Date Joined'),
        default=timezone.now
    )

    language_code = models.CharField(
        verbose_name=_('Language'),
        max_length=10,
        null=True,
        blank=True,
        default=default_language_code
    )

    theme = models.CharField(
        verbose_name=_('Theme'),
        max_length=50,
        choices=[
            (None, (
                ('preset', _('Preset')),
                ('light', _('Light')),
                ('dark', _('Dark')),
                ('custom', _('Custom'))
            ))
        ],
        default='preset'
    )

    objects = UserManager()

    EMAIL_FIELD = 'email'
    USERNAME_FIELD = 'email'

    def __str__(self):
        return self.username or self.email

    def get_absolute_url(self):
        return resolve_url('user:detail')

    def full_name(self):
        return f'{self.first_name or ""}{" " if self.first_name else ""}{self.last_name or ""}'

    def language_code_display(self):
        return LANGUAGE_DISPLAY.get(self.language_code)

    def all_tenants(self):
        tenants = Tenant.objects.filter(members__user=self)
        return tenants

    @staticmethod
    def exclude_from_filter():
        return ['password']
