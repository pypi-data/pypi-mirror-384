from django.contrib import admin
from .models import Theme


class ThemeAdmin(admin.ModelAdmin):
    model = Theme
    list_display = ('pk', 'user', 'tenant')
    search_fields = ('pk', 'user', 'tenant')


admin.site.register(Theme, ThemeAdmin)
