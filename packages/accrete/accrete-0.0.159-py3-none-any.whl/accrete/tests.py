from django.test import TestCase
from django.contrib.auth.models import AnonymousUser
from django.contrib.auth import get_user_model
from django.forms import ValidationError
from django.db.models import ObjectDoesNotExist
from django.views import View
from django.test import Client
from django.test.client import RequestFactory
from django.conf import settings

from accrete import models
from accrete import forms
from .views.mixins import TenantRequiredMixin

User = get_user_model()


class FormTestCase(TestCase):
    def setUp(self):
        self.tenant = models.Tenant(name='Test Tenant')
        self.tenant.save()
        self.user = User(email='test@user.test', username='Test User')
        self.user.save()

    def test_form_set_tenant(self):
        f = forms.Form(tenant=self.tenant.pk, user=self.user.pk)
        self.assertEqual(self.tenant, f.tenant)

    def test_form_set_user(self):
        f = forms.Form(tenant=self.tenant.pk, user=self.user.pk)
        self.assertEqual(self.user, f.user)

    def test_form_tenant_queryset(self):
        f = forms.Form(tenant=self.tenant.pk, user=self.user.pk)
        self.assertEqual(
            list(f.fields['tenant'].queryset),
            list(models.Tenant.objects.filter(pk=self.tenant.pk))
        )

    def test_from_clean_staff(self):
        self.user.is_staff = True
        self.user.save()
        f = forms.Form({
            'tenant': self.tenant
        }, tenant=self.tenant.pk, user=self.user.pk)
        self.assertTrue(f.is_valid())

    def test_form_no_user(self):
        with self.assertRaises(ObjectDoesNotExist):
            forms.Form({'tenant': self.tenant}, tenant=self.tenant.pk)

    def test_form_no_tenant(self):
        with self.assertRaises(ObjectDoesNotExist):
            forms.Form({'tenant': self.tenant}, user=self.user.pk)

    def test_form_not_a_member(self):
        with self.assertRaises(ValidationError):
            f = forms.Form(
                {'tenant': self.tenant},
                tenant=self.tenant.pk, user=self.user.pk
            )
            f.is_valid()
            f.clean()

    def test_form_with_member(self):
        member = models.Member(
            tenant=self.tenant,
            user=self.user
        )
        member.save()
        f = forms.Form(
            {'tenant': self.tenant},
            tenant=self.tenant.pk, user=self.user.pk
        )
        f.is_valid()
        f.clean()

    def test_modelform_set_tenant(self):
        f = forms.Form(tenant=self.tenant.pk, user=self.user.pk)
        self.assertEqual(self.tenant, f.tenant)

    def test_modelform_set_user(self):
        f = forms.Form(tenant=self.tenant.pk, user=self.user.pk)
        self.assertEqual(self.user, f.user)

    def test_modelform_tenant_queryset(self):
        f = forms.Form(tenant=self.tenant.pk, user=self.user.pk)
        self.assertEqual(
            list(f.fields['tenant'].queryset),
            list(models.Tenant.objects.filter(pk=self.tenant.pk))
        )

    def test_modelfrom_clean_staff(self):
        self.user.is_staff = True
        self.user.save()
        f = forms.Form({
            'tenant': self.tenant
        }, tenant=self.tenant.pk, user=self.user.pk)
        self.assertTrue(f.is_valid())

    def test_modelform_no_user(self):
        with self.assertRaises(ObjectDoesNotExist):
            forms.Form({'tenant': self.tenant}, tenant=self.tenant.pk)

    def test_modelform_no_tenant(self):
        with self.assertRaises(ObjectDoesNotExist):
            forms.Form({'tenant': self.tenant}, user=self.user.pk)

    def test_modelform_not_a_member(self):
        with self.assertRaises(ValidationError):
            f = forms.Form(
                {'tenant': self.tenant},
                tenant=self.tenant.pk, user=self.user.pk
            )
            f.is_valid()
            f.clean()

    def test_modelform_with_member(self):
        member = models.Member(
            tenant=self.tenant,
            user=self.user
        )
        member.save()
        f = forms.Form(
            {'tenant': self.tenant},
            tenant=self.tenant.pk, user=self.user.pk
        )
        f.is_valid()
        f.clean()


class MiddlewareTestCase(TestCase):
    def setUp(self):
        self.user = User(email='test@user.test', username='Test User')
        self.user.save()

    def test_no_tenant(self):
        c = Client()
        c.force_login(self.user)
        res = c.get('/')
        self.assertFalse(c.cookies.get('tenant_id'))
        self.assertFalse(res.wsgi_request.tenant)

    def test_get_non_existing(self):
        c = Client()
        c.force_login(self.user)
        res = c.get('/', {'tenant_id': 1})
        self.assertFalse(c.cookies.get('tenant_id'))
        self.assertFalse(res.wsgi_request.tenant)
    
    def test_get_no_member(self):
        tenant = models.Tenant(name='Test Tenant')
        tenant.save()
        c = Client()
        c.force_login(self.user)
        res = c.get('/', {'tenant_id': tenant.pk + 1})
        with self.assertRaises(KeyError):
            cookie = c.cookies['tenant_id']
        self.assertFalse(res.wsgi_request.tenant)
        self.assertFalse(res.wsgi_request.member)

    def test_get(self):
        tenant = models.Tenant(name='Test Tenant')
        tenant.save()
        member = models.Member(
            tenant=tenant,
            user=self.user
        )
        member.save()
        c = Client()
        c.force_login(self.user)
        res = c.get('/')
        self.assertEqual(c.cookies['tenant_id'].value, str(tenant.pk))
        self.assertEqual(res.wsgi_request.tenant, tenant)
        self.assertEqual(res.wsgi_request.member, member)

    def test_post_no_member(self):
        c = Client()
        c.force_login(self.user)
        c.post('/', {'tenant_id': 1})
        self.assertFalse(c.cookies.get('tenant_id'))

    def test_post(self):
        tenant = models.Tenant(name='Test Tenant')
        tenant.save()
        member = models.Member(
            tenant=tenant,
            user=self.user
        )
        member.save()
        c = Client()
        c.force_login(self.user)
        c.post('/', {'tenant_id': tenant.pk})
        self.assertEqual(c.cookies['tenant_id'].value, str(tenant.pk))


class TenantViewTestCase(TestCase):
    class TestView(TenantRequiredMixin, View):
        tenant_url = '/tenant/not/set/'

    def setUp(self):
        self.factory = RequestFactory()
        self.user_without_tenant = User(
            email='test@test.com', username='Test User'
        )
        self.user_without_tenant.save()

    def test_not_logged_in(self):
        request = self.factory.get('/')
        request.user = AnonymousUser()
        view = self.TestView.as_view()
        res = view(request)
        self.assertEqual(res.status_code, 302)
        self.assertEqual(
            res.url.split('?')[0].rstrip('/'),
            settings.LOGIN_URL.rstrip('/')
        )

    def test_no_tenant(self):
        request = self.factory.get('/')
        request.user = self.user_without_tenant
        request.tenant = None
        view = self.TestView.as_view()
        res = view(request)
        self.assertEqual(res.url, '/tenant/not/set/')
