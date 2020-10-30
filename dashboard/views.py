import json

from urllib.parse import urlparse

from django.urls import resolve
from django.shortcuts import render, redirect, get_object_or_404
from django.http import Http404, HttpResponseRedirect, HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate
from django.contrib.auth import login as django_login
from django.contrib.auth import logout as django_logout
from django.core.files.storage import default_storage
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt

from django.contrib.auth.models import User, Group
from rest_framework import viewsets
from rest_framework import permissions
from rest_framework import generics

from .serializers import UserSerializer, GroupSerializer, LogSerializer

from .service import generate_visjs_graph
from .models import Service, SecurityPolicy, Log, Configuration
from .tasks import test, kubernetes_apply, test_echo

@csrf_exempt
def start_test(request):
    if request.method == 'GET':
        test_echo()
    return HttpResponse(status=200)

  
@login_required
def deploy(request, service_id):

    service = get_object_or_404(
        Service, id=service_id, owner_id=request.user.id)

    namespace = service.service_name
    path = service.service_file.path
    orchestrator = request.POST.get('orchestratorSelect', None)

    print(f"Deploy {path} via {orchestrator} at {namespace}")

    if orchestrator == "kubernetes":
        t = kubernetes_apply.delay(path, namespace)
        l = Log(owner=request.user, log_id=t.id, log_status=t.status)
        l.save()

    # t = test.delay("deploy")
    # l = Log(owner=request.user, log_id=t.id, log_status=t.status)
    # l.save()

    # next = request.POST.get('next', '/')
    # return HttpResponseRedirect(next)
    messages.add_message(request, messages.INFO, 'Deployment scheduled',
                        extra_tags='alert alert-primary')

    logs_list = Log.objects.filter(owner_id=request.user.id)
    return render(request, 'dashboard/logs.html',
                  {'logs_list': logs_list})


@login_required
def logs(request):
    # t = test.delay("hello")
    # l = Log(owner=request.user, log_id=t.id, log_status=t.status)
    # l.save()
    logs_list = Log.objects.filter(owner_id=request.user.id)

    return render(request, 'dashboard/logs.html',
                  {'logs_list': logs_list})


@login_required
def service(request, service_id):
    service = Service.objects.get(id=service_id, owner_id=request.user.id)
    allowed_connections = []
    try:
        allowed_connections = json.loads(service.allowed_connections)
        # print(allowed_connections)
    except json.JSONDecodeError:
        pass

    if request.method == 'POST':
        allowed_connections = []
        enabled_policies = []
        for key, value in request.POST.items():
            if "-to-" in key:
                allowed_connections.append(key)
            if "ASTRID_" in key:
                if ".CONFIG" in key:
                    policy_id = key.split(".")[0]
                    policy = get_object_or_404(SecurityPolicy, policy_id=policy_id)
                    config = request.POST[key]
                    try:
                        obj = Configuration.objects.get(service=service, policy=policy)
                        obj.config = config.lstrip(" \t\n")
                        obj.save()
                    except Configuration.DoesNotExist:
                        obj = Configuration(service=service, policy=policy, config=config)
                        obj.save()
                else:
                    enabled_policies.append(key)

        allowed_connections = list(set(allowed_connections))
        service.allowed_connections = json.dumps(allowed_connections)
        service.policies.clear()
        for policy_id in enabled_policies:
            try:
                p = SecurityPolicy.objects.get(policy_id=policy_id)
                service.policies.add(p)
            except SecurityPolicy.DoesNotExist:
                pass

        service.kibana_dashboard = ""
        service.save()

    nodes, edges, all_edges = generate_visjs_graph(service.service_file.read())

    for connection in allowed_connections:
        try:
            edges.append({"from": connection.split('-to-')[0],
                          "to": connection.split('-to-')[1], "arrows": "to",
                          "id": connection, "color": {"color": "red"}})
        except Exception as ex:
            print(ex)

    # print(edges)
    basic_policies = SecurityPolicy.objects.all().filter(policy_sla='B')
    pro_policies = SecurityPolicy.objects.all().filter(policy_sla='P')
    unlimited_policies = SecurityPolicy.objects.all().filter(policy_sla='U')

    service_policies = service.policies.all().values_list('policy_id', flat=True)
    
    service_configurations = {}
    for policy_id in service_policies:
        policy = SecurityPolicy.objects.get(policy_id=policy_id)
        obj, created = Configuration.objects.get_or_create(service=service, policy=policy)
        service_configurations[policy_id] = obj.config.lstrip(" \t\n")

    context = {'nodes': nodes, 'edges': edges, 'all_edges': all_edges,
               'service': service, 'basic_policies': basic_policies,
               'pro_policies': pro_policies,
               'unlimited_policies': unlimited_policies,
               'service_policies': service_policies,
               'allowed_connections': allowed_connections,
               'service_configurations': service_configurations}

    return render(request, 'dashboard/service.html', context)


@login_required
def services(request):
    service_list = Service.objects.filter(owner_id=request.user.id)

    if request.method == 'POST':
        service_name = request.POST['service-name']
        service = Service(owner=request.user, service_name=service_name,
                          service_file=request.FILES['service-file'])
        service.save()

    return render(request, 'dashboard/services.html',
                  {'service_list': service_list})


@login_required
def monitoring(request):
    service_list = Service.objects.filter(owner_id=request.user.id)

    return render(request, 'dashboard/monitoring.html',
                  {'service_list': service_list})


@login_required
def agreements(request):

    return render(request, 'dashboard/agreements.html')


@login_required
def welcome(request):

    return render(request, 'dashboard/welcome.html')


@login_required
def logout(request):
    django_logout(request)

    return redirect('dashboard:login')


def login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        next = request.POST['next']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            django_login(request, user)
            try:
                resolve(urlparse(next))
                return redirect(next)
            except Http404:
                return redirect('dashboard:welcome')
        else:
            messages.add_message(request, messages.ERROR, 'Login failed.',
                                 extra_tags='alert alert-danger')

    next = request.GET['next'] if 'next' in request.GET else None
    return render(request, 'dashboard/login.html', {'next': next})


class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]


class GroupViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows groups to be viewed or edited.
    """
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    permission_classes = [permissions.IsAuthenticated]


class LogViewSet(viewsets.ModelViewSet):
    queryset = Log.objects.all()
    serializer_class = LogSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)