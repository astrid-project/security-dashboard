from django.urls import path
from django.contrib.auth.models import User

from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.welcome, name='welcome'),
    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),
    path('agreements/', views.agreements, name='agreements'),
    path('services/<int:service_id>/', views.service, name='service'),
    path('services/<int:service_id>/deploy', views.deploy, name='deploy'),
    path('editor/<int:service_id>/', views.editor, name="editor"),
    path('customize/<int:service_id>/', views.createSecurityPolicy, name="customize"),
    path('agent/', views.services, name="config"),
    path('agent/<slug:graph_id>/', views.configureAgent, name="config"),
    path('services/', views.services, name='services'),
    path('monitoring/', views.monitoring, name='monitoring'),
    path('logs/', views.logs, name='logs'),
    path('k8resource/', views.get_k8_resource, name="k8resource"),
    path('algorithm/', views.configureAlgorithm, name="algorithm"),
    # path('test/', views.start_test),
]