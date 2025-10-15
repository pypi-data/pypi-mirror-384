from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import views, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden, HttpResponseRedirect
from django.shortcuts import redirect, render, resolve_url
from django.utils.translation import gettext_lazy as _
from django.conf import settings

from accrete.utils import save_form
from accrete.contrib import ui
from accrete.contrib.ui.models import Theme
from accrete.contrib.ui.forms import ThemeForm
from .forms import UserForm, ChangePasswordForm, ChangeEmailForm


class LoginView(views.LoginView):

    form_class = AuthenticationForm
    template_name = 'user/login.html'
    redirect_authenticated_user = True

    def form_invalid(self, form):
        user = form.get_user()
        if user is not None and not user.is_active:
            ctx = {'to_confirm': True}
            if self.extra_context:
                self.extra_context.update(ctx)
            else:
                self.extra_context = ctx
        return super().form_invalid(form)


class LogoutView(views.LogoutView):

    def post(self, request, *args, **kwargs):
        request.skip_htmx_redirect_middleware = True
        res = super().post(request, *args, **kwargs)
        if isinstance(res, HttpResponseRedirect):
            res.headers['HX-Redirect'] = res.url
            res.status_code = 200
        return res

    def get_success_url(self):
        return resolve_url(settings.LOGIN_URL)


@login_required()
def user_detail(request):
    form = UserForm(
        initial={'language_code': request.user.language_code},
        instance=request.user
    )
    theme = Theme.objects.filter(user=request.user).first()
    theme_form = ThemeForm(instance=theme, prefix='theme', initial={'user': request.user})
    refresh = False
    if request.method == 'POST':
        form = save_form(UserForm(request.POST, instance=request.user))
        theme_form = save_form(ThemeForm(request.POST, instance=theme, prefix='theme', initial={'user': request.user}))
        if (form.is_saved or not form.has_changed()) or (theme_form.is_saved or not theme_form.has_changed()):
            refresh = True
    res = ui.WindowResponse(
        title=str(_('User Preferences')),
        overview_template='user/user_preferences.html#data',
        header_template='user/user_preferences.html#header',
        context=dict(user=request.user, form=form, theme_form=theme_form),
        is_centered=True
    ).response(request, replace_body=False)
    if refresh:
        res.headers['HX-Refresh'] = 'true'
    return res


@login_required()
def user_change_password(request):
    if request.user.is_managed:
        return HttpResponseForbidden()
    form = ChangePasswordForm(instance=request.user)
    update = bool(request.method == 'POST')
    if request.method == 'POST':
        form = save_form(ChangePasswordForm(request.POST, instance=request.user))
        if form.is_saved:
            update_session_auth_hash(request, form.instance)
            return redirect(
                resolve_url('user:detail')
                + f'?{request.GET.urlencode()}'
            )
    return ui.ModalResponse(
        title=str(_('Change Password')),
        modal_id='change-password',
        template='user/change_password.html',
        is_update=update,
        context=dict(form=form, user=request.user)
    ).response(request)


@login_required()
def user_change_email(request):
    if request.user.is_managed:
        return HttpResponseForbidden()
    form = ChangeEmailForm(instance=request.user)
    update = bool(request.method == 'POST')
    if request.method == 'POST':
        form = save_form(ChangeEmailForm(request.POST, instance=request.user))
        if form.is_saved:
            return redirect(
                resolve_url('user:detail')
                + f'?{request.GET.urlencode()}'
            )
    return ui.ModalResponse(
        title=str(_('Change E-Mail')),
        modal_id='change-email',
        template='user/change_email.html',
        is_update=update,
        context=dict(form=form, user=request.user)
    ).response(request)


def password_forgotten(request):
    return render(request, 'user/')