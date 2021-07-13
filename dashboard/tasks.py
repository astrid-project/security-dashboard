# Create your tasks here
from __future__ import absolute_import, unicode_literals
import pickle
from bios.base import YAML_FILES
from kafka import KafkaProducer

from celery import Task
from celery import shared_task

from kubernetes import client, config, utils, watch

from dashboard.models import Log
from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder
from django.core import serializers

import yaml
import json
import time
import base64
import requests
import uuid


# Modified version from
# https://github.com/kubernetes-client/python/blob/master/kubernetes/utils/create_from_yaml.py
#
# Copyright 2018 The Kubernetes Authors.
# Licensed under the Apache License, Version 2.0 (the "License");
def create_from_yaml(
        k8s_client,
        yaml_file,
        verbose=False,
        namespace="default",
        **kwargs):
    """
    Perform an action from a yaml file. Pass True for verbose to
    print confirmation information.
    Input:
    yaml_file: dict. YAML file content.
    k8s_client: an ApiClient object, initialized with the client args.
    verbose: If True, print confirmation from the create action.
        Default is False.
    namespace: string. Contains the namespace to create all
        resources inside. The namespace must preexist otherwise
        the resource creation will fail. If the API object in
        the yaml file already contains a namespace definition
        this parameter has no effect.
    Available parameters for creating <kind>:
    :param async_req bool
    :param bool include_uninitialized: If true, partially initialized
        resources are included in the response.
    :param str pretty: If 'true', then the output is pretty printed.
    :param str dry_run: When present, indicates that modifications
        should not be persisted. An invalid or unrecognized dryRun
        directive will result in an error response and no further
        processing of the request.
        Valid values are: - All: all dry run stages will be processed
    Returns:
        The created kubernetes API objects.
    Raises:
        FailToCreateError which holds list of `client.rest.ApiException`
        instances for each object that failed to create.
    """
    #yml_document_all = yaml.safe_load_all(yaml_file)
    yml_document_all = yaml_file

    failures = []
    k8s_objects = []
    for yml_document in yml_document_all:
        try:
            created = utils.create_from_dict(k8s_client, yml_document, verbose,
                                        namespace=namespace,
                                        **kwargs)
            k8s_objects.append(created)
        except utils.FailToCreateError as failure:
            failures.extend(failure.api_exceptions)
    if failures:
        raise utils.FailToCreateError(failures)

    return k8s_objects


class LogTask(Task):

    def on_failure(self, exc, task_id, args, kwargs, einfo):

        log = Log.objects.get(log_id=task_id)
        log.log_status = "FAILURE"
        log.log_message = "{}".format(exec)
        log.save()

        return super().on_failure(exc, task_id, args, kwargs, einfo)

    def on_success(self, retval, task_id, args, kwargs):

        log = Log.objects.get(log_id=task_id)
        log.log_status = "SUCCESS"
        log.log_message = "{}".format(retval)
        log.save()

        return super().on_success(retval, task_id, args, kwargs)
        

@shared_task
def kubernetes_apply(yaml_b64, namespace="default", sc={}):
    config.load_incluster_config()

    aApiClient = client.ApiClient()
    v1 = client.CoreV1Api(aApiClient)
    body = client.V1Namespace(metadata=client.V1ObjectMeta(name=namespace))

    try:
        api_response = v1.create_namespace(body)
    except Exception as api_exception:
        print(api_exception)

    yaml_file = pickle.loads(base64.b64decode(yaml_b64))
    print(yaml_file)

    try:
        #yaml_file = base64.decodebytes(bytes(yaml_b64, "utf-8"))
        create_from_yaml(aApiClient, yaml_file, namespace=namespace)
    except Exception as api_exception:
        print(api_exception)

    agent_list = ['polycube','lcp']
    watch_list = []
    for yaml in yaml_file:
        if yaml["kind"] == "Deployment":
            if "annotations" in yaml["metadata"]:
                for k,v in yaml["metadata"]["annotations"].items():
                    if k in agent_list:
                        port = None
                        if k == "lcp":
                            port = 5000
                        if k == "polycube":
                            port = 4000
                        watch_list.append({"id": v,
                                           "name": k,
                                           "ip": None,
                                           "port": port,
                                           "exec_env_id": "idany",
                                           "arguments": [],
                                           "deployment": yaml["metadata"]["name"]
                                          })
    print(watch_list)

    w = watch.Watch()
    topic = settings.KAFKA_TOPIC
    bootstrap = settings.KAFKA_BOOTSTRAP
    security_controller_notified = False
    security_controller_url = settings.SECURITY_CONTROLLER_URL

    try:
        for event in w.stream(v1.list_namespaced_pod, namespace):
            #print(event)
            msg = json.dumps(event["raw_object"])
            print(msg)

            if event['type'] == 'MODIFIED':
                for i,name in enumerate([d["deployment"] for d in watch_list]):
                    p = event['object']
                    if name in p.metadata.name:
                        agent_ip = p.status.pod_ip
                        watch_list[i]["ip"] = agent_ip
                        
            if not any(v is None for v in [d["ip"] for d in watch_list]):
                if not security_controller_notified:
                    print(sc)
                    if sc['deployment']['pipelines']:
                        sc['deployment']['pipelines'][0]['agents'] = watch_list
                    print(sc)
                    print("send to security controller")
                    msg = json.dumps(sc)
                    print(msg)
                    try:
                        r = requests.post(security_controller_url,data=msg)
                        print(r)
                    except:
                        pass
                    security_controller_notified = True

            # try:
            #     producer = KafkaProducer(bootstrap_servers=bootstrap)
            #     producer.send(topic, msg.encode('utf-8'))
            # except Exception as kafka_exception:
            #     print(kafka_exception)
    except Exception as api_exception:
        print(api_exception)

    return "finished"


@shared_task
def kubernetes_get_pod(name, namespace):
    config.load_incluster_config()

    aApiClient = client.ApiClient()
    v1 = client.CoreV1Api(aApiClient)

    try:
        p = v1.read_namespaced_pod(name=name,namespace=namespace)
        print(p.status.phase, p.status.pod_ip)
    except  Exception as api_exception:
        print(api_exception)

    return "get pod success"


@shared_task
def security_apply_policy(policy, configuration=None):
    # for p in serializers.deserialize("json", policy):
    #     msg = json.dumps(p,cls=DjangoJSONEncoder)
    #     print(msg)
    # if not (configuration is None):
    #     for c in serializers.deserialize("json", configuration):
    #         msg = json.dumps(c,cls=DjangoJSONEncoder)
    #         print(msg)
    topic = settings.KAFKA_TOPIC
    bootstrap = settings.KAFKA_BOOTSTRAP

    j = {}

    p = json.loads(policy)
    j["policy"] = p[0]
    
    if not (configuration is None):
        c = json.loads(configuration)
        j["configuration"] = c[0]
        
    msg = json.dumps(j)
    print(msg)
    try:
        producer = KafkaProducer(bootstrap_servers=bootstrap)
        producer.send(topic, msg.encode('utf-8'))
    except Exception as kafka_exception:
        print(kafka_exception)

    return "policy applied success"


@shared_task
def test_echo():
    echo_server = settings.TEST_ECHO_SERVER

    r = requests.get(echo_server)
    print(r)

    return "echo success"


@shared_task
def test(message):
    return message