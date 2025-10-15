import logging
from urllib.parse import urlparse, parse_qs
from django.contrib.auth import get_user_model

from accrete.models import Tenant, Member
from accrete.tenant import set_member, set_tenant

_logger = logging.getLogger(__name__)


class TenantMiddleware:
    """
    Set tenant and member contextvar
    """

    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        user = scope.get('user')
        if not user or not isinstance(user, get_user_model()):
            set_member(None)
            return await self.inner(scope, receive, send)
        tenant_id = parse_qs(urlparse(
            f"?{scope.get('query_string', b'').decode()}"
        ).query).get('tenant_id', [None])[0]
        tenant = tenant_id and await Tenant.objects.aget(pk=tenant_id)
        if tenant and user.is_staff:
            set_tenant(tenant)
            return await self.inner(scope, receive, send)
        get_kwargs = {'user': user, 'tenant': tenant}
        try:
            member = await Member.objects.aget(**get_kwargs)
        except (Member.DoesNotExist, Member.MultipleObjectsReturned) as e:
            _logger.error(e)
            member = None
        set_member(member)
        return await self.inner(scope, receive, send)

