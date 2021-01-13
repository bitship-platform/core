from django.db import models
from django.contrib.auth.models import User
import uuid
from utils.misc import PythonAppConfig


class Customer(models.Model):
    """
    Users signed up to the site.
    """
    id = models.BigIntegerField(primary_key=True)
    tag = models.CharField(max_length=5, default="0000")
    avatar = models.CharField(max_length=50, null=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    credits = models.FloatField(default=0)
    verified = models.BooleanField(default=False)

    def get_avatar_url(self):
        if self.avatar is not None:
            return f"https://cdn.discordapp.com/avatars/{self.id}/{self.avatar}.png"
        else:
            return "https://cdn.discordapp.com/embed/avatars/1.png"

    def get_active_app_count(self):
        return len(self.app_set.filter(status__in=["bg-success", "bg-info", "bg-danger", "bg-warning"]))

    @property
    def terminated_apps(self):
        return self.settings.display_terminated_apps


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
    config = models.JSONField(default=dict)

    @property
    def config_options(self):
        if self.get_stack_display() == "Python":
            return PythonAppConfig

    @property
    def python(self):
        if self.get_stack_display() == "Python":
            return True
        return False

    @property
    def node(self):
        if self.get_stack_display() == "Node.js":
            return True
        return False

    @property
    def ruby(self):
        if self.get_stack_display() == "Ruby":
            return True
        return False

    @property
    def terminated(self):
        if self.get_status_display() == "Terminated":
            return True
        return False

    def primary_files(self):
        return [file for file in self.folder.file_set.all() if file.name.split(".")[1] == "py"]

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


class Setting(models.Model):
    customer = models.OneToOneField(Customer, primary_key=True, on_delete=models.CASCADE, related_name="settings")
    email_notification = models.BooleanField(default=False)
    app_status_alert = models.BooleanField(default=False)
    down_time_alert = models.BooleanField(default=False)
    maintenance_break_alert = models.BooleanField(default=False)
    new_offers_alert = models.BooleanField(default=False)
    display_terminated_apps = models.BooleanField(default=False)


def upload_location(instance, filename):
    folder = instance.folder
    path = ""
    while folder is not None:
        if folder.name:
            path = f"/{folder.name}" + path
        folder = folder.folder
    return f"{instance.folder.owner.id}" + path + f"/{filename}"


class Folder(models.Model):
    """
    Emulates an app folder
    """
    owner = models.ForeignKey(Customer, on_delete=models.CASCADE, null=True, blank=True)
    app = models.OneToOneField(App, on_delete=models.CASCADE, null=True, blank=True, related_name="folder")
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    folder = models.ForeignKey('self', on_delete=models.CASCADE, null=True, related_name="master", blank=True)
    size = models.FloatField(default=0)
    creation_date = models.DateTimeField(auto_now_add=True, null=True)

    def get_size(self):
        mb_size = self.size//1000000
        if not mb_size:
            return f"{self.size/1000}kb"
        else:
            return f"{mb_size}mb"

    def get_absolute_path(self):
        folder = self
        path = ""
        while folder is not None:
            if folder.name:
                path = f"/{folder.name}" + path
            try:
                folder = folder.folder
            except AttributeError:
                folder = None

        return f"/{self.folder.owner.id}" + path


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
                folder = folder.folder
            except AttributeError:
                folder = None

        return f"/{self.folder.owner.id}" + path + f"/{self.name}"

    def get_size(self):
        mb_size = self.size//1000000
        if not mb_size:
            return f"{self.size/1000}kb"
        else:
            return f"{mb_size}mb"


class Orders(models.Model):
    id = models.BigIntegerField(primary_key=True)
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True)
    transaction_amount = models.FloatField(default=0)
    payer_id = models.CharField(max_length=20)
    payer_email = models.CharField(max_length=30)
    create_time = models.DateTimeField(null=True)
    update_time = models.DateTimeField(null=True)
    status = models.CharField(max_length=15)