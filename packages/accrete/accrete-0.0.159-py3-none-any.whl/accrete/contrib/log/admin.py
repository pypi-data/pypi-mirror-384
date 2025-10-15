from django.contrib import admin
from . import models


class LogConfigFieldInLine(admin.TabularInline):

    model = models.LogConfigField


class LogConfigAdmin(admin.ModelAdmin):

    model = models.LogConfig
    list_display = ('model', 'ignore_errors', 'exclude_fields')
    search_fields = ('pk', 'model')
    list_filter = ['ignore_errors', 'exclude_fields']
    inlines = [LogConfigFieldInLine]


class LogAdmin(admin.ModelAdmin):

    model = models.LogConfig
    list_display = (
        'model', 'field', 'object_id', 'log_date', 'old_value', 'new_value',
        'user', 'tenant'
    )
    search_fields = ('model', 'field', 'object_id', 'old_value')
    list_filter = ['model', 'tenant']


admin.site.register(models.LogConfig, LogConfigAdmin)
admin.site.register(models.Log, LogAdmin)
