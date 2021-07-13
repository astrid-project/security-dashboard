from django.conf import settings
from django.db import models
from django.contrib.auth.models import User

import uuid

class Customer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    email = models.EmailField(blank=True)

    def __str__(self):
        return self.user.username


class Service(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )
    service_name = models.CharField(max_length=200)
    service_file = models.FileField(upload_to='uploads/')
    service_file_b64 = models.TextField(blank=True)
    service_file_orig_b64 = models.TextField(blank=True)
    graph_b64 = models.TextField(blank=True)
    last_modified = models.DateTimeField(auto_now=True)
    allowed_connections = models.TextField(blank=True)
    kibana_dashboard = models.TextField(blank=True)
    uuid = models.UUIDField(default=uuid.uuid4,editable=False)

    def __str__(self):
        return self.service_name


class SecurityPolicyTemplate(models.Model):
    BASIC = 'B'
    PRO = 'P'
    UNLIMITED = 'U'
    CUSTOM = 'C'
    SLA_CHOICES = (
        (BASIC, "Basic"),
        (PRO, "Pro"),
        (UNLIMITED, "Unlimited"),
        (CUSTOM, "Custom")
    )
    policy_sla = models.CharField(max_length=1,
                                  choices=SLA_CHOICES,
                                  default=BASIC)
    policy_name = models.CharField(max_length=200)
    policy_description = models.CharField(max_length=500)
    last_modified = models.DateTimeField(auto_now=True)
    policy_id = models.CharField(max_length=20,unique=True)
    code = models.TextField(blank=True)
    configuration = models.TextField(blank=True)
    
    def __str__(self):
        return self.policy_id


class SecurityPolicy(models.Model):
    BASIC = 'B'
    PRO = 'P'
    UNLIMITED = 'U'
    CUSTOM = 'C'
    SLA_CHOICES = (
        (BASIC, "Basic"),
        (PRO, "Pro"),
        (UNLIMITED, "Unlimited"),
        (CUSTOM, "Custom")
    )
    policy_sla = models.CharField(max_length=1,
                                  choices=SLA_CHOICES,
                                  default=BASIC)
    policy_name = models.CharField(max_length=200)
    policy_description = models.CharField(max_length=500)
    last_modified = models.DateTimeField(auto_now=True)
    policy_id = models.CharField(max_length=20)
    code = models.TextField(blank=True)
    configuration = models.TextField(blank=True)
    active = models.BooleanField(default=False)
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    policy_uuid = models.UUIDField(default=uuid.uuid4,editable=False)
    service_file_b64 = models.TextField(blank=True)
    
    def __str__(self):
        return self.policy_id


class Log(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='logs',
        on_delete=models.CASCADE,
    )
    log_id = models.CharField(max_length=200)
    log_status = models.CharField(max_length=200)
    log_message = models.CharField(max_length=500)
    last_modified = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.log_id


class AgentTemplate(models.Model):
    name = models.CharField(max_length=200)
    agent_id = models.CharField(max_length=20,unique=True)
    partner = models.CharField(max_length=200, blank=True)
    description = models.CharField(max_length=500, blank=True)
    configuration = models.TextField(blank=True)
    image = models.CharField(max_length=200, blank=True)

    def __str__(self) -> str:
        return self.name


class Agent(models.Model):
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    agent_id = models.CharField(max_length=20)
    partner = models.CharField(max_length=200, blank=True)
    description = models.CharField(max_length=500, blank=True)
    configuration = models.TextField(blank=True)
    uuid = models.UUIDField(default=uuid.uuid4,editable=False)
    image = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return self.name


class AlgorithmTemplate(models.Model):
    name = models.CharField(max_length=200)
    algorithm_id = models.CharField(max_length=20,unique=True)
    partner = models.CharField(max_length=200, blank=True)
    description = models.CharField(max_length=500, blank=True)
    configuration = models.TextField(blank=True)

    def __str__(self):
        return self.name


class Algorithm(models.Model):
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    algorithm_id = models.CharField(max_length=20)
    partner = models.CharField(max_length=200, blank=True)
    description = models.CharField(max_length=500, blank=True)
    configuration = models.TextField(blank=True)
    uuid = models.UUIDField(default=uuid.uuid4,editable=False)
    active = models.BooleanField(default=False)

    def __str__(self):
        return self.algorithm_id