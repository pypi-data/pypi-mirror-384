from django.contrib import admin
from . import models


class MemberInLine(admin.TabularInline):

    model = models.Member


class TenantAccessGroupInLine(admin.TabularInline):

    model = models.TenantAccessGroupRel
    extra = 0


class AccessGroupMemberInLine(admin.TabularInline):

    model = models.MemberAccessGroupRel
    extra = 0


class TenantAdmin(admin.ModelAdmin):

    model = models.Tenant
    list_display = ('name', 'is_active', 'pk')
    search_fields = ('pk', 'name')
    list_filter = ['is_active']
    inlines = [TenantAccessGroupInLine, MemberInLine]


class MemberAdmin(admin.ModelAdmin):

    model = models.Member
    list_display = ('user', 'tenant', 'is_active')
    search_fields = ('user__email', 'tenant__name')
    list_filter = ['is_active']
    fields = ['user', 'tenant', 'is_active']
    inlines = [AccessGroupMemberInLine]


class AccessGroupAdmin(admin.ModelAdmin):

    model = models.AccessGroup
    list_display = ('name', 'code', 'apply_on')
    search_fields = ('name', 'code')
    list_filter = ['apply_on']


admin.site.register(models.Tenant, TenantAdmin)
admin.site.register(models.Member, MemberAdmin)
admin.site.register(models.AccessGroup, AccessGroupAdmin)
admin.site.register(models.MemberAccessGroupRel)
admin.site.register(models.TenantAccessGroupRel)
