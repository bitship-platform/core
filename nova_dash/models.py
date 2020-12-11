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

    def get_active_app_count(self):
        return len(self.app_set.filter(status__in=["bg-success", "bg-info", "bg-danger"]))


class App(models.Model):
    """
    User's running applications.
    """
    STATUS_CHOICES = [
        ("bg-success", "Running"),
        ("bg-info", "Paused"),
        ("bg-danger", "Stopped"),
        ("bg-dark", "Terminated"),
    ]
    STACK_CHOICES = [
        ("https://cdn.discordapp.com/attachments/785734963458342973/786641902782251028/python.png", "Python"),
        ("https://cdn.discordapp.com/attachments/785734963458342973/786647100749774908/node-js.png", "Node.js"),
        ("https://cdn.discordapp.com/attachments/785734963458342973/786646064878845982/ruby.png", "Ruby"),
    ]
    TYPE_CHOICES = [
        (1.2, "Base"),
        (2.4, "Standard"),
        (4.99, "Premium"),
    ]
    name = models.CharField(max_length=50, default="nova-app")
    owner = models.ForeignKey(Customer, on_delete=models.CASCADE)
    status = models.CharField(choices=STATUS_CHOICES, default="STOPPED", max_length=20)
    stack = models.URLField(choices=STACK_CHOICES, default="Python")
    plan = models.FloatField(choices=TYPE_CHOICES)
    cpu = models.IntegerField(default=0)


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

