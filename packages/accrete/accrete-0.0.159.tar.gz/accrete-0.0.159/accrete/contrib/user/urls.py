from django.urls import path
from . import views

app_name = 'user'

urlpatterns = [
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('detail/', views.user_detail, name='detail'),
    path('password/', views.user_change_password, name='change_password'),
    path('email/', views.user_change_email, name='change_email')
]
