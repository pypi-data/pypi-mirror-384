from django.urls import path

from . import views

app_name = 'ui'

urlpatterns = [
    path('filter/<str:model>/params/', views.params, name='filter_params'),
    path('filter/<str:model>/input/', views.set_filter_input, name='filter_input'),
    path('filter/<str:model>/query/add/', views.filter_add_query, name='filter_add_query')
]
