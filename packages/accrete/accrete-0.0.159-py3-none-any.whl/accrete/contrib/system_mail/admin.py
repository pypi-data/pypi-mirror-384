from django.contrib import admin
from . import models


class SystemMailAdmin(admin.ModelAdmin):
    list_display = ('to_addr', 'from_name', 'subject', 'sent', 'error')


admin.site.register(models.SystemMail, SystemMailAdmin)
