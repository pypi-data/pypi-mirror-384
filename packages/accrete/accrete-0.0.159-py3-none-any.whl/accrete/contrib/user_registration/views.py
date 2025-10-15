import logging

from django.views.generic import FormView, View
from django.urls import reverse_lazy, reverse
from django.contrib.auth import get_user_model
from django.template.loader import render_to_string
from django.shortcuts import render

from accrete.contrib.system_mail.forms import SystemMailCreateForm
from . forms import UserRegistrationForm, ConfirmRegistrationForm, ResendConfirmationMailForm
from . import config

_logger = logging.getLogger(__name__)
User = get_user_model()


def send_confirmation_mail(user, request):
    base = request.build_absolute_uri('/').strip('/')
    endpoint = reverse(
        'user_registration:confirmation', kwargs={'token': user.token.token}
    )
    confirmation_url = f"{base}{endpoint}"

    body = render_to_string(
        config.ACCRETE_USER_REGISTRATION_TEMPLATE_NAME,
        context={'confirmation_url': confirmation_url}
    )

    mail = SystemMailCreateForm({
        'from_name': config.ACCRETE_USER_REGISTRATION_MAIL_FROM_NAME,
        'to_addr': user.email,
        'subject': config.ACCRETE_USER_REGISTRATION_MAIL_SUBJECT,
        'body': body
    })

    if mail.errors:
        _logger.error(
            f"Validation Error while creating system mail for user registration\n"
            f"{dict(mail.errors)}"
        )
        return

    mail.save()


class RegistrationView(FormView):
    form_class = UserRegistrationForm
    template_name = 'user_registration/registration.html'
    success_url = reverse_lazy('user_registration:registration_mail_sent')

    def dispatch(self, request, *args, **kwargs):
        if not config.ACCRETE_USER_REGISTRATION_ALLOWED:
            return self.http_method_not_allowed(request, *args, **kwargs)
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        user = form.save()
        send_confirmation_mail(user, self.request)
        return render(
            self.request,
            'user_registration/registration_confirmation_mail_sent.html',
            {'email': user.email}
        )


class ResendConfirmationMailView(FormView):
    form_class = ResendConfirmationMailForm
    template_name = 'user_registration/confirmation_resend.html'

    def form_valid(self, form):
        email = form.cleaned_data['email']
        user = User.objects.filter(email=email).first()

        if user and not user.is_active:
            send_confirmation_mail(user, self.request)

        return render(
            self.request,
            'user_registration/registration_confirmation_mail_sent.html',
            {'email': email, 'resent': True}
        )


class ConfirmRegistrationView(View):
    @staticmethod
    def get(request, *args, **kwargs):
        form = ConfirmRegistrationForm({'token': kwargs.get('token')})
        if form.is_valid():
            form.save()
            return render(request, 'user_registration/confirmation_succeeded.html', {})
        return render(
            request, 'user_registration/confirmation_failed.html', {
                'form': form
            }
        )
