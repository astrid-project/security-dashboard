from django.urls import path

from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.welcome, name='welcome'),
    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),
    path('agreements/', views.agreements, name='agreements'),
    path('services/<int:service_id>/', views.service, name='service'),
    path('services/', views.services, name='services'),
    path('monitoring/', views.monitoring, name='monitoring'),
]
