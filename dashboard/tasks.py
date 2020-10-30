# Create your tasks here
from __future__ import absolute_import, unicode_literals

from celery import Task
from celery import shared_task

from kubernetes import client, config, utils

from dashboard.models import Log
from django.conf import settings

import requests


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
def kubernetes_apply(yaml_file, namespace="default"):
    config.load_incluster_config()

    aApiClient = client.ApiClient()
    v1 = client.CoreV1Api(aApiClient)
    body = client.V1Namespace(metadata=client.V1ObjectMeta(name=namespace))

    try:
        api_response = v1.create_namespace(body)
    except Exception as api_exception:
        print(api_exception)

    try:
        utils.create_from_yaml(aApiClient, yaml_file, namespace=namespace)
    except Exception as api_exception:
        print(api_exception)

    return "apply submitted"


@shared_task
def test_echo():
    echo_server = settings.TEST_ECHO_SERVER

    r = requests.get(echo_server)
    print(r)

    return "echo success"


@shared_task
def test(message):
    return message