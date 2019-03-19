from django.conf import settings
from django.db import models

class Service(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )
    service_name = models.CharField(max_length=200)
    service_file = models.FileField(upload_to='uploads/')
    last_modified = models.DateTimeField(auto_now=True)
    allowed_connections = models.TextField(blank=True)

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
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    policy_name = models.CharField(max_length=200)
    policy_description = models.CharField(max_length=500)
    policy_enabled = models.BooleanField(default=False)
    last_modified = models.DateTimeField(auto_now=True)
