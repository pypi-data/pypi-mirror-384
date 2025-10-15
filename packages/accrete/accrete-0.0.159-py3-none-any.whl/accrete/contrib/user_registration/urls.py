from django.urls import path

from . import views

app_name = 'user_registration'

urlpatterns = [
    path('register/', views.RegistrationView.as_view(), name='registration'),
    path('mail_resend/', views.ResendConfirmationMailView.as_view(), name='registration_resend_mail'),
    path('confirmation/<str:token>/', views.ConfirmRegistrationView.as_view(), name='confirmation')
]
