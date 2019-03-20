import json

from urllib.parse import urlparse

from django.urls import resolve
from django.shortcuts import render, redirect
from django.http import HttpResponse, Http404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate
from django.contrib.auth import login as django_login
from django.contrib.auth import logout as django_logout
from django.core.files.storage import default_storage

from django.views import generic

from .forms import UploadFileForm
from .service import generate_visjs_graph
from .models import Service, SecurityPolicy



@login_required
def security(request, service_id):
    service = Service.objects.get(id=service_id, owner_id=request.user.id)
    allowed_connections = []
    try:
        allowed_connections = json.loads(service.allowed_connections)
    except json.JSONDecodeError:
        pass

    if request.method == 'POST':
        allowed_connections = []
        enabled_policies = []
        for key, value in request.POST.items():
            if "-to-" in key:
                allowed_connections.append(key)
            if "ASTRID_" in key:
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

        service.save()

    nodes, edges, all_edges = generate_visjs_graph(default_storage.open(service.service_file))

    for connection in allowed_connections:
        try:
            edges.append({"from": connection.split('-to-')[0],
                          "to": connection.split('-to-')[1], "arrows": "to",
                          "id": connection, "color": {"color": "red"}})
        except Exception as ex:
            print(ex)

    basic_policies = SecurityPolicy.objects.all().filter(policy_sla='B')
    pro_policies = SecurityPolicy.objects.all().filter(policy_sla='P')
    unlimited_policies = SecurityPolicy.objects.all().filter(policy_sla='U')

    service_policies = service.policies.all().values_list('policy_id', flat=True)

    context = {'nodes': nodes, 'edges': edges, 'all_edges': all_edges,
               'service': service, 'basic_policies': basic_policies,
               'pro_policies': pro_policies,
               'unlimited_policies': unlimited_policies,
               'service_policies': service_policies,
               'allowed_connections': allowed_connections}

    return render(request, 'dashboard/security.html', context)


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
def slas(request):

    return render(request, 'dashboard/slas.html')


@login_required
def index(request):
    # form = UploadFileForm()
    # with open('/home/benjamin/code/astrid/dashboard/test/docker-compose.yml') as f:
    #     nodes, edges = generate_visjs_graph(f)
    nodes, edges = dict(), dict()
    return render(request, 'dashboard/index.html',
                  {"nodes": nodes, "edges": edges})


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
            except Http404:
                return redirect('dashboard:index')

        return redirect(next)

    next = request.GET['next'] if 'next' in request.GET else None
    return render(request, 'dashboard/login.html', {'next': next})
