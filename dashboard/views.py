import re
import json
import base64
import pickle
import bios
import urllib
import uuid
import copy
from itertools import chain

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
from kubernetes.client import configuration
from rest_framework import viewsets
from rest_framework import permissions
from rest_framework import generics

from .serializers import UserSerializer, GroupSerializer, LogSerializer

from .service import generate_visjs_graph
from .models import Algorithm, Service, SecurityPolicy, SecurityPolicyTemplate, Log, Agent, AgentTemplate, AlgorithmTemplate
from .tasks import test, kubernetes_apply, kubernetes_get_pod, test_echo, security_apply_policy
from .forms import CubebeatForm, AlgorithmForm

sc = {'name': 'astrid-agent', 'image': 'busybox', 'command': ['/bin/sh'], 'args': ['-c','while true; do sleep 5; done']}


@csrf_exempt
def healthCheck(request):
    return HttpResponse(status=200)


def get_k8_resource(request):
    namespace = request.GET.get('namespace', None)
    label = request.GET.get('label', None)
    print(f'{namespace} {label}')

    # s = json.loads(label)
    # selector = ','.join([f'{k}={s[k]}' for k in s])

    response = {}

    try:
        config.load_incluster_config()

        aApiClient = client.ApiClient()
        v1 = client.CoreV1Api(aApiClient)

        res = v1.list_namespaced_pod(namespace)

        j = {}
        for item in res.items:
            d = item.to_dict()
            if label in [c['name'] for c in d['spec']['containers']]:
                j = {"host_ip": d["status"]["host_ip"], 
                    "pod_ip": d["status"]["pod_ip"], 
                    "phase": d["status"]["phase"], 
                    "start_time": d["status"]["start_time"], 
                    "containers": [{"name": status["name"],
                                    "ready": status["ready"]} for status in d["status"]["container_statuses"]]}

            response = json.dumps(j, cls=DjangoJSONEncoder)
    except:
        pass

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
    yaml_b64 = service.service_file_b64
    enabled_policies = SecurityPolicy.objects.all().filter(service=service,active=True)
    enabled_algorithms = Algorithm.objects.all().filter(service=service,active=True)

    algorithms = [
        {
            "id": a.uuid,
            "name": a.name,
            "arguments": []

        } for a in enabled_algorithms]

    pipelines = [
        {
            "id": p.policy_uuid,
            "name": p.policy_name,
            "status": "started",
            "agents": [],
            "algorithms": algorithms,
            "configuration": p.configuration
        } for p in enabled_policies]

    sc = {
        "deployment": {
            "id": service.uuid,
            "name": service.service_name,
            "namespace": service.service_name,
            "pipelines": pipelines
        }
    }

    orchestrator = request.POST.get('orchestratorSelect', None)

    print(f"Deploy via {orchestrator} at {namespace}")
    print(sc)
        
    if orchestrator == "kubernetes":
        t = kubernetes_apply.delay(yaml_b64, namespace, sc)
        l = Log(owner=request.user, log_id=t.id,
                log_message=f"watching {namespace}", log_status=t.status)
        l.save()

    return redirect(reverse('dashboard:service', kwargs={'service_id': service_id}))

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
        # policy, created = SecurityPolicy.objects.update_or_create(
        #     policy_sla = 'C',
        #     policy_name = 'Custom-' + str(uuid.uuid4()),
        #     policy_description = "custom security service",
        #     policy_id = 'ASTRID_5555'
        # )
        # service = Service.objects.get(id=service_id, owner_id=request.user.id)
        # service.policies.add(policy)
        # service.save()
        pass

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
    # if request.method == 'POST':
    #     print(request.POST)
    #     conf_str = json.dumps(request.POST)
    #     print(conf_str)

    #     service_id = request.POST.get('service_id', None)
    #     name = request.POST.get('name', None)
    #     partner = request.POST.get('partner', None)

    #     service = Service.objects.get(id=service_id, owner_id=request.user.id)

    #     agent, created = Agent.objects.update_or_create(
    #         service = service,
    #         graph_id = graph_id,
    #         name = name,
    #         partner = partner,
    #         defaults={'config': conf_str},
    #     )

    #     return redirect(reverse('dashboard:editor', kwargs={'service_id': service_id}))

    agent = Agent.objects.get(uuid=graph_id)
    print(agent)
    
    graph = pickle.loads(base64.b64decode(agent.service.graph_b64))
    nodes = graph['nodes']
    edges = graph['edges']

    # print(nodes)
    # print(edges)

    agents = AgentTemplate.objects.all()
    algorithms = AlgorithmTemplate.objects.all()

    context = {'nodes': nodes, 'edges': edges,
               'service': agent.service,
               'agents': agents, 'algorithms': algorithms,
               'agent': agent}

    return render(request, 'dashboard/editor.html', context)


@login_required
def editor(request, service_id):
    service = Service.objects.get(id=service_id, owner_id=request.user.id)
    
    if request.method == 'POST':
        data = None
        try:
            data = json.loads(request.body)
            print(data)
        except:
            print("ERROR")

        yaml_b64 = service.service_file_b64
        yaml_file = pickle.loads(base64.b64decode(yaml_b64))

        if data:
            for d in data:
                if d["connections"]:
                    for y in yaml_file:
                        if y['metadata']['annotations']['graphId'] == d['id']:
                            for c in d["connections"]:
                                at = AgentTemplate.objects.get(name=c)
                                a = Agent(
                                    service=service,
                                    name=at.name,
                                    agent_id=at.agent_id,
                                    partner=at.partner,
                                    description=at.description,
                                    configuration=at.configuration,
                                    image=at.image
                                )
                                a.save()
                                container = {'image': a.image, 'name': a.name, 'args': ['sleep', '1000']}
                                y["spec"]["template"]["spec"]["containers"].append(container)
                                y['metadata']['annotations'][a.name] = str(a.uuid)
        else:
            Algorithm.objects.all().filter(service=service,active=True).update(active=False)
            enabled = False
            for k,v in request.POST.items():
                print(k,v)
                if re.match(r'ASTRID_\d+$',k):
                    print("create/update algorithm from template")
                    enabled = True
                    try:
                        a = Algorithm.objects.get(service=service,algorithm_id=v)
                        a.active = True
                        a.save()
                    except:
                        at = AlgorithmTemplate.objects.get(algorithm_id=v)
                        a = Algorithm(
                            service=service,
                            name=at.name,
                            algorithm_id=at.algorithm_id,
                            partner=at.partner,
                            description=at.description,
                            active=True
                        )
                        a.save()
            for k,v in request.POST.items():
                if re.match(r'ASTRID_\d+\.ALGORITHM.CONFIG$',k) and enabled:
                    if v:
                        print("update configuration")
                        algorithm_id = k.split('.')[0]
                        a = Algorithm.objects.get(service=service,algorithm_id=algorithm_id)
                        a.configuration = v.lstrip(" \t\n")
                        a.save()

            try:
                pipelineName = request.POST["pipelineName"]
                pipeline = SecurityPolicy.objects.get(service=service,policy_name=pipelineName)
                pipeline.active = True
                pipeline.save()
            except:
                id_num = 111111
                try:
                    latest = SecurityPolicy.objects.latest('policy_id')
                    id_num = int(latest.policy_id.split('_')[1])
                except:
                    pass
                pipeline = SecurityPolicy(
                    service=service,
                    policy_sla="C",
                    policy_name=pipelineName,
                    policy_description="Custom policy",
                    policy_id=f"ASTRID_{id_num + 1}",
                    active=True
                )
                pipeline.save()

        yaml_file, nodes, edges = generate_visjs_graph(yaml_file)
        service.service_file_b64 = str(base64.b64encode(
            pickle.dumps(yaml_file)), "utf-8")
        service.graph_b64 = str(base64.b64encode(
            pickle.dumps({'nodes': nodes, 'edges': edges})), "utf-8")    
        service.save()

        pipeline.service_file_b64 = str(base64.b64encode(
            pickle.dumps(yaml_file)), "utf-8")
        pipeline.save()

        return redirect(reverse('dashboard:service', kwargs={'service_id': service_id}))

    graph = pickle.loads(base64.b64decode(service.graph_b64))
    nodes = graph['nodes']
    edges = graph['edges']

    # print(nodes)
    # print(edges)

    agents = AgentTemplate.objects.all()
    algorithms = AlgorithmTemplate.objects.all()

    enabled_algorithms = Algorithm.objects.all().filter(service=service,active=True).values_list('algorithm_id', flat=True)

    context = {'nodes': nodes, 'edges': edges,
               'service': service,
               'agents': agents, 'algorithms': algorithms,
               'enabled_algorithms': enabled_algorithms}

    return render(request, 'dashboard/editor.html', context)

    
@login_required
def service(request, service_id):
    service = Service.objects.get(id=service_id, owner_id=request.user.id)

    if request.method == 'POST':
        SecurityPolicy.objects.all().filter(service=service,active=True).update(active=False)
        yaml_b64 = service.service_file_orig_b64
        yaml_file = pickle.loads(base64.b64decode(yaml_b64))
        yaml_file, nodes, edges = generate_visjs_graph(yaml_file)
        service.service_file_b64 = str(base64.b64encode(
            pickle.dumps(yaml_file)), "utf-8")
        service.graph_b64 = str(base64.b64encode(
            pickle.dumps({'nodes': nodes, 'edges': edges})), "utf-8")    
        service.save()

        enabled = False
        for k,v in request.POST.items():
            if re.match(r'ASTRID_\d+$',k):
                print("create/update policy from template")
                enabled = True
                try:
                    p = SecurityPolicy.objects.get(service=service,policy_id=v)
                    p.active = True
                    p.save()
                except:
                    policy = SecurityPolicyTemplate.objects.get(policy_id=v)
                    p = SecurityPolicy(
                        policy_sla = policy.policy_sla,
                        policy_name = policy.policy_name,
                        policy_description = policy.policy_description,
                        policy_id = policy.policy_id,
                        service = service,
                        active = True
                    )
                    p.save()
        for k,v in request.POST.items():
            if re.match(r'ASTRID_\d+\.CONFIG$',k) and enabled:
                if v:
                    print("update configuration")
                    policy_id = k.split('.')[0]
                    p = SecurityPolicy.objects.get(service=service,policy_id=policy_id)
                    p.configuration = v.lstrip(" \t\n")
                    p.save()
        for k,v in request.POST.items():
            if re.match(r'ASTRID_\d+\.CODE$',k) and enabled:
                if v:
                    print("update code")
                    policy_id = k.split('.')[0]
                    p = SecurityPolicy.objects.get(service=service,policy_id=policy_id)
                    p.code = v.lstrip(" \t\n")
                    p.save()
                    print("exec code")
                    OUTPUT = ""
                    yaml_b64 = service.service_file_b64
                    yaml_file = pickle.loads(base64.b64decode(yaml_b64))
                    exec(v)
                    print(yaml_file)

                    yaml_file, nodes, edges = generate_visjs_graph(yaml_file)
                    service.service_file_b64 = str(base64.b64encode(
                        pickle.dumps(yaml_file)), "utf-8")
                    service.graph_b64 = str(base64.b64encode(
                        pickle.dumps({'nodes': nodes, 'edges': edges})), "utf-8")    

                    service.save()
                else:
                    print("update graph")
                    policy_id = k.split('.')[0]
                    p = SecurityPolicy.objects.get(service=service,policy_id=policy_id)
                    yaml_b64 = p.service_file_b64
                    yaml_file = pickle.loads(base64.b64decode(yaml_b64))
                    yaml_file, nodes, edges = generate_visjs_graph(yaml_file)
                    service.service_file_b64 = str(base64.b64encode(
                        pickle.dumps(yaml_file)), "utf-8")
                    service.graph_b64 = str(base64.b64encode(
                        pickle.dumps({'nodes': nodes, 'edges': edges})), "utf-8")    

                    service.save()

    graph = pickle.loads(base64.b64decode(service.graph_b64))
    nodes = graph['nodes']
    edges = graph['edges']

    basic_policies = SecurityPolicyTemplate.objects.all().filter(policy_sla='B')
    pro_policies = SecurityPolicyTemplate.objects.all().filter(policy_sla='P')
    unlimited_policies = SecurityPolicyTemplate.objects.all().filter(policy_sla='U')
    custom_policies = SecurityPolicyTemplate.objects.all().filter(policy_sla='C')
    custom_service_policies = SecurityPolicy.objects.all().filter(service=service,policy_sla='C')
    cp = [p for p in custom_service_policies if not p.policy_name in custom_policies.values_list('policy_name', flat=True)]
    custom_policies = list(custom_policies) + list(cp)
    #custom_policies = (custom_policies | custom_service_policies).distinct()
    service_policies = SecurityPolicy.objects.all().filter(service=service)
    
    enabled_policies = SecurityPolicy.objects.all().filter(service=service,active=True).values_list('policy_id', flat=True)
    

    #service_policies = service.policies.filter(active=True).values_list('policy_id', flat=True)
    
    # service_configurations = {}
    # for policy_id in service_policies:
    #     policy = SecurityPolicy.objects.get(policy_id=policy_id)
    #     service_configurations[policy_id] = policy.configuration

    context = {'nodes': nodes, 'edges': edges,
               'service': service, 'basic_policies': basic_policies,
               'pro_policies': pro_policies,
               'unlimited_policies': unlimited_policies,
               'custom_policies': custom_policies,
               'service_policies': service_policies,
               'enabled_policies': enabled_policies}

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

        yaml_file, nodes, edges = generate_visjs_graph(yaml_file)

        service.service_file_b64 = str(base64.b64encode(
            pickle.dumps(yaml_file)), "utf-8")
        service.service_file_orig_b64 = str(base64.b64encode(
            pickle.dumps(yaml_file)), "utf-8")
        service.graph_b64 = str(base64.b64encode(
            pickle.dumps({'nodes': nodes, 'edges': edges})), "utf-8")    

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