from django.db import models
from django.contrib.auth.models import User


class Customer(models.Model):
    id = models.BigIntegerField(primary_key=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    credits = models.IntegerField(default=0)
    join_date = models.DateTimeField(auto_now_add=True)


class Nodes(models.Model):
    id = models.BigIntegerField(primary_key=True)
    name = models.CharField(max_length=100, blank=True, null=True)
