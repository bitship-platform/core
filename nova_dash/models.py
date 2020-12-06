from django.db import models
from django.contrib.auth.models import User


class Customer(models.Model):
    """
    Users signed up to the site.
    """
    id = models.BigIntegerField(primary_key=True)
    avatar = models.URLField(null=True, blank=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    credits = models.IntegerField(default=0)
    join_date = models.DateTimeField(auto_now_add=True)
    address = models.TextField(null=True, blank=True)
    pincode = models.IntegerField(null=True, blank=True)



class App(models.Model):
    """
    User's running applications.
    """
    STATUS_CHOICES = [
        ("RUNNING", "RUNNING"),
        ("PAUSED", "PAUSED"),
        ("STOPPED", "STOPPED"),
        ("TERMINATED", "TERMINATED"),
    ]
    TYPE_CHOICES = [
        (1.2, "BASE"),
        (2.4, "STANDARD"),
        (4.99, "PREMIUM"),
    ]
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    status = models.CharField(choices=STATUS_CHOICES, default="STOPPED", max_length=20)
    plan = models.FloatField(choices=TYPE_CHOICES)
