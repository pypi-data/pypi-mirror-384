from django.contrib import admin
from .models import Country


class CountryAdmin(admin.ModelAdmin):
    model = Country
    list_display = ('name', 'iso_code_a2', 'iso_code_a3', 'vat_prefix', 'order_priority')
    search_fields = ('name', 'iso_code_a2', 'iso_code_a3', 'vat_prefix')


admin.site.register(Country, CountryAdmin)
