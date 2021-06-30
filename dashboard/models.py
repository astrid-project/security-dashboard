from django.conf import settings
from django.db import models
from django.contrib.auth.models import User


class Customer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    email = models.EmailField(blank=True)

    def __str__(self):
        return self.user.username


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
    policy_id = models.CharField(max_length=20, unique=True)

    def __str__(self):
        return self.policy_id


class Service(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )
    service_name = models.CharField(max_length=200)
    service_file = models.FileField(upload_to='uploads/')
    service_file_b64 = models.TextField(blank=True)
    last_modified = models.DateTimeField(auto_now=True)
    allowed_connections = models.TextField(blank=True)
    kibana_dashboard = models.TextField(blank=True)
    policies = models.ManyToManyField(SecurityPolicy, blank=True)

    def __str__(self):
        return self.service_name


class Configuration(models.Model):
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    policy = models.ForeignKey(SecurityPolicy, on_delete=models.CASCADE)
    active = models.BooleanField(default=False)
    config = models.TextField()

    class Meta:
        unique_together = ["service", "policy"]


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


class Agent(models.Model):
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    graph_id = models.CharField(max_length=200, unique=True)
    name = models.CharField(max_length=200)
    partner = models.CharField(max_length=200, blank=True)
    description = models.CharField(max_length=500, blank=True)
    config = models.TextField(blank=True)

    def __str__(self):
        return self.graph_id


class AgentTemplate(models.Model):
    name = models.CharField(max_length=200)
    partner = models.CharField(max_length=200, blank=True)
    description = models.CharField(max_length=500, blank=True)
    config = models.TextField(blank=True)

    def __str__(self) -> str:
        return self.name


class Algorithm(models.Model):
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    algorithm_id = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=200)
    partner = models.CharField(max_length=200, blank=True)
    description = models.CharField(max_length=500, blank=True)
    config = models.TextField(blank=True)

    def __str__(self):
        return self.algorithm_id


class AlgorithmTemplate(models.Model):
    name = models.CharField(max_length=200)
    algorithm_id = models.CharField(max_length=20, unique=True)
    partner = models.CharField(max_length=200, blank=True)
    description = models.CharField(max_length=500, blank=True)
    config = models.TextField(blank=True)

    def __str__(self):
        return self.name