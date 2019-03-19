from django.urls import path

from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.index, name='index'),
    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),
    path('sla/', views.slas, name='slas'),
    path('services/<int:service_id>/', views.security, name='security'),
    path('services/', views.services, name='services'),
]
