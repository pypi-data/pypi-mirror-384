import logging

from django import forms
from django.core.validators import validate_email

from .models import SystemMail
from .tasks import run_mail_queue

_logger = logging.getLogger(__name__)


class SystemMailCreateForm(forms.ModelForm):

    class Meta:
        model = SystemMail
        fields = [
            'from_name',
            'to_addr',
            'subject',
            'body'
        ]

    def clean_to_addr(self):
        emails = self.cleaned_data['to_addr']
        for email in emails.split(','):
            if email:
                validate_email(email)
        return emails

    def save(self, commit=True):
        super().save(commit)
        if commit:
            run_mail_queue.delay()
        return self.instance
