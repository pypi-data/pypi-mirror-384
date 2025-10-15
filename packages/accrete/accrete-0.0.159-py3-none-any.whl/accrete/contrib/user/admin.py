from django.contrib import admin
from django import forms
from .models import User


class UserForm(forms.ModelForm):

    login = forms.CharField(
        required=False
    )

    email = forms.EmailField(
        required=False
    )


class UserAdmin(admin.ModelAdmin):

    model = User
    form = UserForm
    list_display = (
        'username',
        'email',
        'login',
        'first_name',
        'last_name'
    )
    search_fields = [
        'email',
        'login',
        'username',
        'first_name',
        'last_name'
    ]
    list_filter = [
        'is_superuser',
        'is_staff',
        'is_active',
        'is_managed'
    ]


admin.site.register(User, UserAdmin)
