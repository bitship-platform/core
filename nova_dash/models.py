from django.db import models
from django.contrib.auth.models import User


class Customer(models.Model):
    """
    Users signed up to the site.
    """
    id = models.BigIntegerField(primary_key=True)
    tag = models.CharField(max_length=5, default="0000")
    avatar = models.CharField(max_length=50, null=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    credits = models.IntegerField(default=0)
    join_date = models.DateTimeField(auto_now_add=True)

    def get_avatar_url(self):
        if self.avatar is not None:
            return f"https://cdn.discordapp.com/avatars/{self.id}/{self.avatar}.png"
        else:
            return "https://cdn.discordapp.com/embed/avatars/1.png"


class App(models.Model):
    """
    User's running applications.
    """
    STATUS_CHOICES = [
        ("bg-success", "RUNNING"),
        ("bg-orange", "PAUSED"),
        ("bg-info", "STOPPED"),
        ("bg-danger", "TERMINATED"),
    ]
    TYPE_CHOICES = [
        (1.2, "BASE"),
        (2.4, "STANDARD"),
        (4.99, "PREMIUM"),
    ]
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    status = models.CharField(choices=STATUS_CHOICES, default="STOPPED", max_length=20)
    plan = models.FloatField(choices=TYPE_CHOICES)


class Address(models.Model):
    """
    Billing addresses of the verified users
    """
    customer = models.OneToOneField(Customer, primary_key=True, on_delete=models.CASCADE)
    firstname = models.CharField(max_length=50, null=True)
    lastname = models.CharField(max_length=50, null=True)
    location = models.TextField(null=True)
    city = models.CharField(max_length=100, null=True)
    country = models.CharField(max_length=100, null=True)
    pincode = models.IntegerField(null=True)

