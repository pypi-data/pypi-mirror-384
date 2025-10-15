import logging

from django.utils.deprecation import MiddlewareMixin
from accrete.tenant import set_tenant, set_member, get_tenant

from .models import Tenant, Member

_logger = logging.getLogger(__name__)


class TenantMiddleware(MiddlewareMixin):

    @staticmethod
    def get_tenant_id_from_request(request):
        tenant_id = (
            request.GET.get('tenant_id')
            or request.META.get('HTTP_X_TENANT_ID')
        )
        try:
            tenant_id = int(tenant_id)
            assert tenant_id > 0
        except (ValueError, TypeError, AssertionError):
            tenant_id = None
        return tenant_id

    def process_request(self, request):
        request.tenant = None
        request.member = None
        set_member(False)
        if request.path.startswith('/admin'):
            return
        if not request.user.is_authenticated:
            set_member(None)
            return
        tenant_id = self.get_tenant_id_from_request(request)
        tenant = Tenant.objects.none()
        memberships = Member.objects.filter(
            user=request.user, is_active=True, tenant__is_active=True
        ).prefetch_related('tenant', 'user').order_by('pk')
        if tenant_id:
            tenant = Tenant.objects.get(pk=tenant_id)
            memberships = memberships.filter(tenant=tenant)
        membership_count = memberships.count()
        if membership_count == 1:
            request.member = memberships.first()
            request.tenant = request.member.tenant
            set_member(request.member)
            self.update_post_data(request)
            return
        if membership_count > 1:
            set_member(None)
            return
        if request.user.is_staff and tenant:
            set_member(None)
            set_tenant(tenant)
            request.tenant = tenant
            return
        set_member(None)
        return

    @staticmethod
    def update_post_data(request):
        if request.POST and not request.POST.get('tenant') and request.tenant:
            request.POST = request.POST.copy()
            request.POST['tenant'] = request.tenant.pk

    @staticmethod
    def process_response(request, response):
        tenant = get_tenant()
        response['X-TENANT-ID'] = tenant and tenant.id or 0
        return response
