from .tenant import get_tenant, get_member


def tenant(request):
    return {
        'member': get_member(),
        'tenant': get_tenant()
    }
