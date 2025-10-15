import os
from urllib.parse import urljoin
from django.core.files.storage import FileSystemStorage
from django.utils.encoding import filepath_to_uri
from django.utils.deconstruct import deconstructible
from django.conf import settings
from accrete.tenant import get_tenant


@deconstructible(path="django.core.files.storage.FileSystemStorage")
class TenantFileSystemStorage(FileSystemStorage):

    @property
    def base_location(self):
        tenant = get_tenant()
        base_dir = f'{settings.MEDIA_ROOT}/{tenant.id}'
        os.makedirs(os.path.dirname(base_dir), exist_ok=True)
        return base_dir

    @property
    def location(self):
        return os.path.abspath(self.base_location)

    @property
    def base_url(self):
        if self._base_url is not None and not self._base_url.endswith("/"):
            self._base_url += "/"
        res = self._value_or_setting(
            self._base_url,
            f'{settings.MEDIA_URL.strip("/")}/{get_tenant().id}'
        )
        return res

    def url(self, name):
        if self.base_url is None:
            raise ValueError("This file is not accessible via a URL.")
        url = filepath_to_uri(name)
        if url is not None:
            url = url.lstrip("/")
        return urljoin(f'/{self.base_url}/', url)
