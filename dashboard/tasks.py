# Create your tasks here
from __future__ import absolute_import, unicode_literals

from celery import Task
from celery import shared_task

from kubernetes import client, config

from dashboard.models import Log


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
    config.load_kube_config(config_file='/home/dev/Programming/ASTRID/config')
    v1 = client.CoreV1Api()
    print("Listing pods with their IPs:")
    ret = v1.list_pod_for_all_namespaces(watch=False)
    for i in ret.items:
        print("%s\t%s\t%s" % (i.status.pod_ip, i.metadata.namespace, i.metadata.name))

    return "apply complete"


@shared_task
def test(message):
    return message