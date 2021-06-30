import json
import base64
import pickle
import bios
import urllib
import uuid

from kubernetes import config, client

from urllib.parse import urlparse

from django.urls import resolve, reverse
from django.shortcuts import render, redirect, get_object_or_404
from django.http import Http404, HttpResponseRedirect, HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate
from django.contrib.auth import login as django_login
from django.contrib.auth import logout as django_logout
from django.core.files.storage import default_storage
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.core.serializers.json import DjangoJSONEncoder
from django.core import serializers

from django.contrib.auth.models import User, Group
from rest_framework import viewsets
from rest_framework import permissions
from rest_framework import generics

from .serializers import UserSerializer, GroupSerializer, LogSerializer

from .service import generate_visjs_graph
from .models import Algorithm, Service, SecurityPolicy, Log, Configuration, Agent, AgentTemplate, AlgorithmTemplate
from .tasks import test, kubernetes_apply, kubernetes_get_pod, test_echo, security_apply_policy
from .forms import CubebeatForm, AlgorithmForm

sc = {'name': 'astrid-agent', 'image': 'busybox', 'command': ['/bin/sh'], 'args': ['-c','while true; do sleep 5; done']}


@csrf_exempt
def healthCheck(request):
    return HttpResponse(status=200)


def get_k8_resource(request):
    namespace = request.GET.get('namespace', None)
    labels = request.GET.get('labels', None)
    print(f'{namespace} {labels}')

    s = json.loads(labels)
    selector = ','.join([f'{k}={s[k]}' for k in s])

    response = {}
    try:
        config.load_incluster_config()

        aApiClient = client.ApiClient()
        v1 = client.CoreV1Api(aApiClient)

        res = v1.list_namespaced_pod(namespace,label_selector=selector)

        j = {}
        for item in res.items: 
            d = item.to_dict() 
            j = {"host_ip": d["status"]["host_ip"], 
                "pod_ip": d["status"]["pod_ip"], 
                "phase": d["status"]["phase"], 
                "start_time": d["status"]["start_time"], 
                "containers": [{"name": status["name"],
                                "ready": status["ready"]} for status in d["status"]["container_statuses"]]}

        response = json.dumps(j, cls=DjangoJSONEncoder)

    except Exception as ex:
        print(ex)

    return JsonResponse(response, safe=False)


# @csrf_exempt
# def start_test(request):
#     if request.method == 'GET':
#         test_echo()
#     return HttpResponse(status=200)


@csrf_exempt
def k8events(request):
    u = User.objects.filter(username='system')

    if not u:
        u = User.objects.create_user('system', 'system@astrid.local', 'system')
    else:
        u = User.objects.get(username='system')
    try:
        s = json.loads(request.body)
        if s["reason"] == "Started":
            if s["involvedObject"]["kind"] == "Pod":
                pod_name = s["involvedObject"]["name"]
                pod_namespace = s["involvedObject"]["namespace"]

                t = kubernetes_get_pod.delay(pod_name, pod_namespace)
                l = Log(owner=u, log_id=t.id, log_status=t.status)
                l.save()
    except Exception as ex:
        print(ex)

    return HttpResponse(status=200)


@login_required
def deploy(request, service_id):

    service = get_object_or_404(
        Service, id=service_id, owner_id=request.user.id)

    namespace = service.service_name
    #path = service.service_file.path
    yaml_b64 = service.service_file_b64
    orchestrator = request.POST.get('orchestratorSelect', None)

    print(f"Deploy via {orchestrator} at {namespace}")

    if orchestrator == "kubernetes":
        t = kubernetes_apply.delay(yaml_b64, namespace)
        l = Log(owner=request.user, log_id=t.id,
                log_message=f"watching {namespace}", log_status=t.status)
        l.save()

    # t = test.delay("deploy")
    # l = Log(owner=request.user, log_id=t.id, log_status=t.status)
    # l.save()

    # next = request.POST.get('next', '/')
    # return HttpResponseRedirect(next)
    messages.add_message(request, messages.INFO, 'Deployment scheduled',
                        extra_tags='alert alert-primary')

    logs_list = Log.objects.filter()
    return render(request, 'dashboard/logs.html',
                  {'logs_list': logs_list})


@login_required
def logs(request):
    # t = test.delay("hello")
    # l = Log(owner=request.user, log_id=t.id, log_status=t.status)
    # l.save()
    logs_list = Log.objects.filter()

    return render(request, 'dashboard/logs.html',
                  {'logs_list': logs_list})


@login_required
def createSecurityPolicy(request, service_id):
    if request.method == 'POST':
        policy, created = SecurityPolicy.objects.update_or_create(
            policy_sla = 'C',
            policy_name = 'Custom-' + str(uuid.uuid4()),
            policy_description = "custom security service",
            policy_id = 'ASTRID_5555'
        )
        service = Service.objects.get(id=service_id, owner_id=request.user.id)
        service.policies.add(policy)
        service.save()

    return redirect(reverse('dashboard:service', kwargs={'service_id': service_id}))


@login_required
def configureAlgorithm(request):
    context = {}
    if request.method == 'POST':
        print(request.POST)
        algorithm_id = request.POST.get('id', 'ASTRID_9999')
    
    algorithm_id = 'ASTRID_9999'
    algorithm = AlgorithmTemplate.objects.get(algorithm_id=algorithm_id)
    form = AlgorithmForm()

    context = {"algorithm": algorithm, "form": form}
        
    return render(request, 'dashboard/algorithm.html', context)


@login_required
def configureAgent(request, graph_id):
    context = {}
    if request.method == 'POST':
        print(request.POST)
        conf_str = json.dumps(request.POST)
        print(conf_str)

        service_id = request.POST.get('service_id', None)
        name = request.POST.get('name', None)
        partner = request.POST.get('partner', None)

        service = Service.objects.get(id=service_id, owner_id=request.user.id)

        agent, created = Agent.objects.update_or_create(
            service = service,
            graph_id = graph_id,
            name = name,
            partner = partner,
            defaults={'config': conf_str},
        )

        return redirect(reverse('dashboard:editor', kwargs={'service_id': service_id}))

    agent = Agent.objects.get(graph_id=graph_id)
    print(agent)

    config = json.loads(agent.config)
    enabled = True
    period = "12s"

    if "enabled" in config:
        enabled = config["enabled"]
    if "period" in config:
        period = config["period"]

    data = {"service_id": agent.service.id, "name": agent.name,
            "partner": agent.partner,
            "enabled": enabled, "period": period}
    print(data)
    
    form = CubebeatForm(data)
    context = {'agent': agent, 'form': form}

    return render(request, 'dashboard/config.html', context)


@login_required
def editor(request, service_id):
    service = Service.objects.get(id=service_id, owner_id=request.user.id)
    allowed_connections = []
    try:
        allowed_connections = json.loads(service.allowed_connections)
        # print(allowed_connections)
    except json.JSONDecodeError:
        pass

    yaml_b64 = service.service_file_b64
    yaml_file = pickle.loads(base64.b64decode(yaml_b64))

    message = None
    if request.method == 'POST':
        connections = request.body
        d = json.loads(connections)
        print(connections)

        for item in yaml_file: 
            if item["kind"] == "Deployment": 
                name = item["metadata"]["name"] 
                containers = item["spec"]["template"]["spec"]["containers"] 
                print(name, containers) 
                connections = list(filter(lambda x: name in x["label"] and x["kind"] == "Deployment", d))[0]["connections"].copy() 
                print(name, connections) 
                new_containers = [] 

                for container in containers: 
                    if container["name"] in connections: 
                        new_containers.append(container) 
                        connections.remove(container["name"]) 
                for connection in connections:
                    new_containers.append({'name': connection, 'image': 'busybox', 'command': ['/bin/sh'], 'args': ['-c','while true; do sleep 5; done']})

                item["spec"]["template"]["spec"]["containers"] = new_containers
        
        service.service_file_b64 = str(base64.b64encode(
            pickle.dumps(yaml_file)), "utf-8")
        service.save()

        message = "Successfully saved"

    nodes, edges, all_edges = generate_visjs_graph(yaml_file)

    for connection in allowed_connections:
        try:
            edges.append({"from": connection.split('-to-')[0],
                          "to": connection.split('-to-')[1], "arrows": "to",
                          "id": connection, "color": {"color": "red"}})
        except Exception as ex:
            print(ex)

    print(message)

    agents = AgentTemplate.objects.all()
    algorithms = AlgorithmTemplate.objects.all()

    context = {'nodes': nodes, 'edges': edges, 'all_edges': all_edges,
               'service': service, 'agents': agents, 'algorithms': algorithms,
               'allowed_connections': allowed_connections,
               'message': message}

    return render(request, 'dashboard/editor.html', context)


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

                policy = serializers.serialize("json", [p,])
                policy_conf = None

                try:
                    c = Configuration.objects.get(policy=p.pk)
                    policy_conf = serializers.serialize("json", [c,])
                except Configuration.DoesNotExist as ex:
                    print(ex)
                
                t = security_apply_policy.delay(policy, policy_conf)
                l = Log(owner=request.user, log_id=t.id,
                        log_message=f"apply policy {p.policy_name}",
                        log_status=t.status)
                l.save()
                
            except SecurityPolicy.DoesNotExist as ex:
                print(ex)

        service.kibana_dashboard = ""
        service.save()

    yaml_b64 = service.service_file_b64
    yaml_file = pickle.loads(base64.b64decode(yaml_b64))

    nodes, edges, all_edges = generate_visjs_graph(yaml_file)

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
    custom_policies = SecurityPolicy.objects.all().filter(policy_sla='C')

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
               'custom_policies': custom_policies,
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

        yaml_file = bios.read(service.service_file.path, file_type='yaml')

        # for item in yaml_file:
        #     if item.get("kind",None) == "Deployment":
        #         item["spec"]["template"]["spec"]["containers"].append(sc)

        service.service_file_b64 = str(base64.b64encode(
            pickle.dumps(yaml_file)), "utf-8")
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