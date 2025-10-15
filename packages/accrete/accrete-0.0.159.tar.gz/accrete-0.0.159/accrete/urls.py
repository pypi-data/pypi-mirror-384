from django.urls import path, include
from django.conf import settings
from accrete.views import get_tenant_file


urlpatterns = [
    path(f'{settings.MEDIA_URL.strip("/")}/<int:tenant_id>/<path:filepath>', get_tenant_file)
]
