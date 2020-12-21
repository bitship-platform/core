from django.db import models
from django.contrib.auth.models import User
import uuid


class Customer(models.Model):
    """
    Users signed up to the site.
    """
    id = models.BigIntegerField(primary_key=True)
    tag = models.CharField(max_length=5, default="0000")
    avatar = models.CharField(max_length=50, null=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    credits = models.FloatField(default=0)
    join_date = models.DateTimeField(auto_now_add=True)

    def get_avatar_url(self):
        if self.avatar is not None:
            return f"https://cdn.discordapp.com/avatars/{self.id}/{self.avatar}.png"
        else:
            return "https://cdn.discordapp.com/embed/avatars/1.png"

    def get_active_app_count(self):
        return len(self.app_set.filter(status__in=["bg-success", "bg-info", "bg-danger", "bg-warning"]))


class App(models.Model):
    """
    User's running applications.
    """
    STATUS_CHOICES = [
        ("bg-warning", "Not Started"),
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
    ram = models.IntegerField(default=0)
    disk = models.IntegerField(default=0)
    network = models.IntegerField(default=0)
    glacier = models.IntegerField(default=0)
    folder = models.OneToOneField("Folder", on_delete=models.SET_NULL, null=True, blank=True)

    @staticmethod
    def get_status_color(value):
        if value > 20:
            if value > 40:
                if value > 60:
                    if value > 80:
                        color_cls = "bg-gradient-danger"
                    else:
                        color_cls = "bg-gradient-warning"
                else:
                    color_cls = "bg-gradient-primary"
            else:
                color_cls = "bg-gradient-info"
        else:
            color_cls = "bg-gradient-success"
        return color_cls


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


def upload_location(instance, filename):
    folder = instance.folder
    path = ""
    while folder is not None:
        print(folder)
        if folder.name:
            path = f"/{folder.name}" + path
        try:
            folder = folder.master.all()[0]
        except IndexError:
            break
    x = f"{instance.folder.owner.id}" + path + f"/{filename}"
    return x


class Folder(models.Model):
    """
    Emulates an app folder
    """
    owner = models.ForeignKey(Customer, on_delete=models.CASCADE, null=True, blank=True)
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    folder = models.ForeignKey('self', on_delete=models.CASCADE, null=True, related_name="master", blank=True)
    size = models.FloatField(default=0)
    creation_date = models.DateTimeField(auto_now_add=True, null=True)

    def get_master(self):
        return self.folder


class File(models.Model):
    folder = models.ForeignKey(Folder, on_delete=models.CASCADE)
    name = models.CharField(max_length=25)
    size = models.FloatField(default=0)
    item = models.FileField(upload_to=upload_location)
    creation_date = models.DateTimeField(auto_now_add=True, null=True)

    def get_absolute_path(self):
        folder = self.folder
        path = ""
        while folder is not None:
            if folder.name:
                path = f"/{folder.name}" + path
            try:
                folder = folder.master
            except AttributeError:
                folder = None

        return f"/{self.folder.owner.id}" + path + f"/{self.name}"