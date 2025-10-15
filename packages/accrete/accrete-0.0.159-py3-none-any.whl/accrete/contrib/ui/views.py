import json
from django.contrib.auth.decorators import login_required
from django.views.generic import View
from django.utils.translation import gettext_lazy as _
from django.apps import apps
from django.http import HttpResponse
from accrete.views import TenantRequiredMixin
from accrete.models import AccessGroup
from accrete.contrib.ui.filter import Filter
from accrete.contrib.ui.response import WindowResponse, ModalResponse


class TenantView(TenantRequiredMixin, View):

    """
    Base View that handles displaying access denied messages
    to the user if member/tenant groups are missing.
    """

    def handle_tenant_group_not_set(self):
        if not self._is_htmx():
            return self._access_denied_page_response()
        return self._access_denied_modal_response()

    def handle_member_group_not_set(self):
        if not self._is_htmx():
            return self._access_denied_page_response()
        return self._access_denied_modal_response()

    def _access_denied_page_response(self):
        return WindowResponse(
            title=str(_('Access Denied')),
            overview_template='mirox/base/group_not_set.html',
            context=dict(groups=self._get_group_data()),
            is_centered=True
        ).response(self.request)

    def _access_denied_modal_response(self):
        res = ModalResponse(
            template='mirox/base/group_not_set_modal.html',
            title=str(_('Access Denied')),
            modal_id='group-missing-modal',
            context=dict(groups=self._get_group_data())
        ).response(self.request)
        res.headers['HX-Reswap'] = 'none'
        res.headers['HX-Push-Url'] = 'false'
        return res

    def _get_group_data(self) -> dict:
        data = {}
        tenant_groups, member_groups = self._flat_groups()
        if tenant_groups:
            data.update(tenant_groups=[])
            access_groups = AccessGroup.objects.filter(
                code__in=tenant_groups,
                apply_on='tenant'
            ).all()
            group_data = {item[0]: item[1] for item in access_groups.values_list('code', 'name')}
            for group in self.TENANT_GROUPS:
                if isinstance(group, tuple):
                    data['tenant_groups'].append(' & '.join([group_data.get(g, g) for g in group]))
                else:
                    data['tenant_groups'].append(group_data.get(group, group))
        if member_groups:
            data.update(member_groups=[])
            access_groups = AccessGroup.objects.filter(
                code__in=member_groups,
                apply_on='member'
            ).all()
            group_data = {item[0]: item[1] for item in access_groups.values_list('code', 'name')}
            for group in self.MEMBER_GROUPS:
                if isinstance(group, tuple):
                    data['member_groups'].append(' & '.join([group_data.get(g, g) for g in group]))
                else:
                    data['member_groups'].append(group_data.get(group, group))
        return data

    def _flat_groups(self) -> tuple[list[str], list[str]]:
        def group_list(g):
            if isinstance(g, str):
                return [g]
            elif isinstance(g, tuple):
                return [x for x in g]
            return []
        tenant_groups = []
        member_groups = []
        for group in self.TENANT_GROUPS:
            tenant_groups.extend(group_list(group))
        for group in self.MEMBER_GROUPS:
            member_groups.extend(group_list(group))
        return tenant_groups, member_groups

    def _is_htmx(self):
        return self.request.headers.get('HX-Request', 'false') == 'true'


@login_required
def params(request, model: str):
    app_label, model_name = model.split('.')
    Model = apps.get_model(app_label, model_name)
    return HttpResponse(Filter(Model, request.GET).query_params())


@login_required
def set_filter_input(request, model: str):
    app_label, model_name = model.split('.')
    Model = apps.get_model(app_label, model_name)
    lookup = request.GET.get('lookup')
    return HttpResponse(Filter(Model, request.GET).query_input(lookup))


@login_required
def filter_add_query(request, model: str):
    app_label, model_name = model.split('.')
    Model = apps.get_model(app_label, model_name)
    query = json.loads(request.GET.get('q', '[]'))
    lookup = request.GET.get('filter_lookup')
    value = request.GET.get('filter_input')
    query.append({lookup: value})
    query = json.dumps(query)
    query_dict = request.GET.copy()
    query_dict.update(q=query)
    return HttpResponse(Filter(Model, query_dict).query_tags())
