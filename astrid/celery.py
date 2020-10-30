from __future__ import absolute_import, unicode_literals

import os
import requests

from celery import Celery


# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'astrid.settings')

# app = Celery('astrid', broker='redis://localhost',
#              backend='redis://localhost', task_cls='dashboard.tasks:LogTask')
app = Celery('astrid', task_cls='dashboard.tasks:LogTask')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()

# @app.on_after_finalize.connect
# def setup_periodic_tasks(sender, **kwargs):
#     sender.add_periodic_task(10.0, periodic_echo.s(), name='add every 10')


# @app.task
# def periodic_echo():
#     echo_server = "http://172.26.0.3:31115"

#     r = requests.get(echo_server)
#     print(r)

#     return "echo success"

@app.task(bind=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request))
