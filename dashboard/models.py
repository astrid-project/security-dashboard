from django.conf import settings
from django.db import models

class Service(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )
    service_file = models.FileField(upload_to='uploads/')
