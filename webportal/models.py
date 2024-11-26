from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    pass


class Material(models.Model):
    name = models.CharField(max_length=255, null=False, blank=False)

    def __str__(self):
        return self.name
