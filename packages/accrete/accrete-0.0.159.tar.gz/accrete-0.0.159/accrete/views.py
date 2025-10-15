import os
from functools import wraps
from typing import Callable

from django.http import HttpResponse, HttpResponseNotFound, HttpResponseForbidden, HttpRequest
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import login_required
from django.core.exceptions import ImproperlyConfigured
from django.shortcuts import redirect, get_object_or_404, resolve_url
from django.conf import settings
from accrete.models import Tenant, Member
from accrete.tenant import get_tenant, tenant_has_group, member_has_group
from accrete import config


class TenantRequiredMixin(LoginRequiredMixin):

    # Redirect to the specified url if the group check fails
    TENANT_NOT_SET_URL = None
    GROUP_NOT_SET_URL = None

    # If set, one of the supplied groups must be present on the
    # tenant or member respectively. If the list item is of type tuple,
    # all the groups in the tuple must be present.
    TENANT_GROUPS: list[str | tuple[str]] = []
    MEMBER_GROUPS: list[str | tuple[str]] = []

    def dispatch(self, request, *args, **kwargs):
        if not self.get_tenant():
            return self.handle_tenant_not_set()
        if self.request.user.is_superuser:
            return super().dispatch(request, *args, **kwargs)
        if not self.check_tenant_group():
            return self.handle_tenant_group_not_set()
        if not self.check_member_group():
            return self.handle_member_group_not_set()
        return super().dispatch(request, *args, **kwargs)

    def handle_tenant_not_set(self):
        return redirect(
            resolve_url(self.get_tenant_not_set_url())
            + f'?next={self.request.get_full_path_info()}'
        )

    def handle_tenant_group_not_set(self):
        return redirect(self.get_group_not_set_url())

    def handle_member_group_not_set(self):
        return redirect(self.get_group_not_set_url())

    def get_tenant_not_set_url(self):
        tenant_not_set_url = (
            self.TENANT_NOT_SET_URL
            or config.ACCRETE_TENANT_NOT_SET_URL
        )
        if not tenant_not_set_url:
            cls_name = self.__class__.__name__
            raise ImproperlyConfigured(
                f"{cls_name} is missing the tenant_not_set_url attribute. "
                f"Define {cls_name}.TENANT_NOT_SET_URL, "
                f"settings.ACCRETE_TENANT_NOT_SET_URL, or override "
                f"{cls_name}.get_tenant_not_set_url()."
            )
        return tenant_not_set_url

    def get_group_not_set_url(self):
        group_not_set_url = (
            self.GROUP_NOT_SET_URL
            or config.ACCRETE_GROUP_NOT_SET_URL
        )
        if not group_not_set_url:
            cls_name = self.__class__.__name__
            raise ImproperlyConfigured(
                f"{cls_name} is missing the group_not_set_url attribute. "
                f"Define {cls_name}.GROUP_NOT_SET_URL, "
                f"settings.ACCRETE_GROUP_NOT_SET_URL, or override "
                f"{cls_name}.get_group_not_set_url()."
            )
        return group_not_set_url

    def check_tenant_group(self) -> bool:
        if not self.TENANT_GROUPS:
            return True
        for group in self.TENANT_GROUPS:
            if isinstance(group, tuple) and all([tenant_has_group(g) for g in group]):
                return True
            elif tenant_has_group(group):
                return True
        return False

    def check_member_group(self) -> bool:
        if not self.MEMBER_GROUPS:
            return True
        for group in self.MEMBER_GROUPS:
            if isinstance(group, tuple) and all([member_has_group(g) for g in group]):
                return True
            elif member_has_group(group):
                return True
        return False

    @staticmethod
    def get_tenant():
        return get_tenant()


def tenant_required(
        tenant_groups: list[str | tuple[str]] = None,
        member_groups: list[str | tuple[str]] = None,
        group_missing_action: str | Callable[[
            HttpRequest, list[str | tuple[str]], list[str | tuple[str]]
        ], HttpResponse] = None,
        redirect_field_name: str = None,
        login_url: str = None
):
    def decorator(f):
        @wraps(f)
        @login_required(
            redirect_field_name=redirect_field_name,
            login_url=login_url
        )
        def _wrapped_view(request, *args, **kwargs):

            def handle_group_missing():
                if callable(group_missing_action):
                    return group_missing_action(
                        request, tenant_groups, member_groups
                    )
                return (
                    redirect(config.ACCRETE_GROUP_NOT_SET_URL)
                    if config.ACCRETE_GROUP_NOT_SET_URL
                    else HttpResponseForbidden()
                )

            tenant = request.tenant
            if not tenant:
                return redirect(config.ACCRETE_TENANT_NOT_SET_URL)
            for tenant_group in (tenant_groups or []):
                if isinstance(tenant_group, tuple) and all([
                    tenant_has_group(g) for g in tenant_group
                ]):
                    break
                elif isinstance(tenant_group, str) and tenant_has_group(tenant_group):
                    break
                return handle_group_missing()
            for member_group in (member_groups or []):
                if isinstance(member_group, tuple) and all([
                    member_has_group(g) for g in member_group
                ]):
                    break
                elif isinstance(member_group, str) and member_has_group(member_group):
                    break
                return handle_group_missing()
            return f(request, *args, **kwargs)
        return _wrapped_view
    return decorator


@tenant_required()
def get_tenant_file(request, tenant_id, filepath):
    tenant = get_object_or_404(Tenant, pk=tenant_id)
    if not request.user.is_staff:
        member = Member.objects.filter(user=request.user, tenant=tenant)
        if not member.exists():
            return HttpResponseNotFound()
    filepath = f'{settings.MEDIA_ROOT}/{tenant_id}/{filepath}'
    if not os.path.exists(filepath):
        return HttpResponseNotFound()
    with open(filepath, 'rb') as f:
        return HttpResponse(f)
