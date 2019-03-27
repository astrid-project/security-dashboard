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
    SLA_CHOICES = (
        (BASIC, "Basic"),
        (PRO, "Pro"),
        (UNLIMITED, "Unlimited")
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
    last_modified = models.DateTimeField(auto_now=True)
    allowed_connections = models.TextField(blank=True)
    kibana_dashboard = models.TextField(blank=True)
    policies = models.ManyToManyField(SecurityPolicy, blank=True)

    def __str__(self):
        return self.service_name
