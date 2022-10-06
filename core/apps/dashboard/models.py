import uuid
from datetime import datetime, timezone

from django.db import models
from django.contrib.auth.models import User
from django.template.defaultfilters import slugify
from utils.misc import PythonAppConfig, NodeAppConfig


class Member(models.Model):
    id = models.BigIntegerField(primary_key=True)
    tag = models.CharField(max_length=5, default="0000")
    avatar = models.CharField(max_length=50, null=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="member")
    verified = models.BooleanField(default=False)
    banned = models.BooleanField(default=False)
    creation_date = models.DateTimeField(null=True, blank=True)

    def get_avatar_url(self):
        if self.avatar is not None:
            return f"https://cdn.discordapp.com/avatars/{self.id}/{self.avatar}.png"
        else:
            return "https://cdn.discordapp.com/embed/avatars/1.png"

    def get_active_app_count(self):
        return len(self.app_set.filter(status__in=["bg-success", "bg-info", "bg-danger", "bg-warning"]))

    def reset(self):
        self.coins = 0
        self.coins_redeemed = 0
        self.credits_spend = 0
        self.app_set.all().delete()
        self.order.all().delete()
        self.verified = False
        self.save()

    @property
    def running_apps(self):
        return len(self.app_set.filter(status__in=["bg-success", "bg-danger"]))

    @property
    def terminated_apps(self):
        return self.settings.display_terminated_apps

    @property
    def get_orders(self):
        return self.order.all().order_by("-create_time")

    @property
    def dark_mode(self):
        return self.settings.dark_mode

    def __str__(self):
        return f"{self.user.first_name} #{self.tag}"


class Team(models.Model):
    id = models.SlugField(auto_created=True, primary_key=True)
    name = models.CharField(max_length=30)
    created_by = models.ForeignKey(Member, on_delete=models.CASCADE, related_name="created_teams")
    members = models.ManyToManyField(Member, related_name="teams")

    @classmethod
    def team_id_setter(cls, instance, **kwargs):
        if not instance.id:
            instance.link = slugify(instance.name)


class TeamPrivilege(models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    member = models.ForeignKey(Member, on_delete=models.CASCADE)
    read = models.BooleanField(default=True)
    edit = models.BooleanField(default=False)
    manage = models.BooleanField(default=False)
    admin = models.BooleanField(default=False)


class App(models.Model):
    STATUS_CHOICES = [
        ("bg-warning", "Not Started"),
        ("bg-success", "Running"),
        ("bg-info", "Pending"),
        ("bg-danger", "Stopped"),
        ("bg-dark", "Terminated"),
    ]
    DEPLOYMENT_STATUS_CHOICES = [
        ("bg-success", "success"),
        ("bg-danger", "failed"),
        ("bg-warning", "pending"),
        ("bg-dark", "rejected"),
        ("bg-secondary", "Not deployed"),
    ]
    STACK_CHOICES = [
        ("https://cdn.discordapp.com/attachments/785734963458342973/786641902782251028/python.png", "Python"),
        ("https://cdn.discordapp.com/attachments/785734963458342973/786647100749774908/node-js.png", "Node.js"),
        ("https://cdn.discordapp.com/attachments/785734963458342973/786646064878845982/ruby.png", "Ruby"),
    ]
    name = models.CharField(max_length=50, default="nova-app")
    unique_id = models.UUIDField(default=uuid.uuid4, null=True)
    team = models.ForeignKey(Team, on_delete=models.CASCADE, null=True)
    status = models.CharField(choices=STATUS_CHOICES, default="STOPPED", max_length=20)
    stack = models.URLField(choices=STACK_CHOICES, default="Python")
    disk = models.IntegerField(default=0, null=True)
    config = models.JSONField(default=dict)
    last_deployment_timestamp = models.DateTimeField(null=True, blank=True)
    last_deployment_status = models.CharField(choices=DEPLOYMENT_STATUS_CHOICES, default="Not deployed", max_length=20)

    @property
    def config_options(self):
        if self.get_stack_display() == "Python":
            return PythonAppConfig
        if self.get_stack_display() == "Node.js":
            return NodeAppConfig

    @property
    def python(self):
        return self.get_stack_display() == "Python"

    @property
    def node(self):
        return self.get_stack_display() == "Node.js"

    @property
    def ruby(self):
        return self.get_stack_display() == "Ruby"

    @property
    def terminated(self):
        return self.get_status_display() == "Terminated"

    @property
    def running(self):
        return self.get_status_display() == "Running"

    @property
    def pending(self):
        return self.last_deployment_status == "bg-warning"

    @property
    def failed(self):
        return self.last_deployment_status == "bg-danger"

    @property
    def success(self):
        return self.last_deployment_status == "bg-success"

    @property
    def rejected(self):
        return self.last_deployment_status == "bg-dark"

    @property
    def idle(self):
        return self.get_status_display() in ["Pending", "Not Started", "Stopped"]

    @property
    def primary_file_set(self):
        return [file.name for file in self.folder.file_set.all()]

    @property
    def requirements(self):
        if self.python:
            if "requirements.txt" in self.primary_file_set:
                return True
            elif "Pipfile" in self.primary_file_set:
                return True
        elif self.node:
            if "package.json" in self.primary_file_set:
                return True
        return False

    @property
    def configuration(self):
        if self.python:
            return "python_version" and "app_json" and "main_executable" in self.config
        elif self.node:
            return "node_version" and "app_json" and "start_script" in self.config

    @property
    def app_stack(self):
        return self.get_stack_display()

    @property
    def app_status(self):
        return self.get_status_display()

    def primary_files(self):
        primary_file_list = []
        file_extension = "py"
        if self.node:
            file_extension = "js"
        for file in self.folder.file_set.all():
            try:
                if file.name.split(".")[1] == file_extension:
                    primary_file_list.append(file)
            except IndexError:
                pass
        return primary_file_list

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


class Setting(models.Model):
    customer = models.OneToOneField(Member, primary_key=True, on_delete=models.CASCADE, related_name="settings")
    email_notification = models.BooleanField(default=False)
    app_status_alert = models.BooleanField(default=False)
    down_time_alert = models.BooleanField(default=False)
    maintenance_break_alert = models.BooleanField(default=False)
    display_terminated_apps = models.BooleanField(default=False)
    beta_tester = models.BooleanField(default=False)


def upload_location(instance, filename):
    folder = instance.folder
    path = ""
    while folder is not None:
        if folder.name:
            path = f"/{folder.name}" + path
        folder = folder.folder
    return f"{instance.folder.team.id}" + path + f"/{filename}"


class Folder(models.Model):
    """
    Emulates an app folder
    """
    team = models.ForeignKey(Team, on_delete=models.CASCADE, null=True, blank=True)
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

        return f"/{self.folder.team.id}" + path


class File(models.Model):
    folder = models.ForeignKey(Folder, on_delete=models.CASCADE)
    name = models.CharField(max_length=25)
    size = models.FloatField(default=0)
    item = models.FileField(upload_to=upload_location, null=True)
    creation_date = models.DateTimeField(auto_now_add=True, null=True)
    system_file = models.BooleanField(default=False)

    class Meta:
        unique_together = ['folder', 'name']

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

        return f"/{self.folder.team.id}" + path + f"/{self.name}"

    def get_size(self):
        mb_size = self.size//1000000
        if not mb_size:
            return f"{self.size/1000}kb"
        else:
            return f"{mb_size}mb"


class Activity(models.Model):
    ACTIVITY_STATUS = (
        ("fa-times-circle text-danger", "Failed"),
        ("fa-clock text-warning", "Pending"),
        ("fa-check-circle text-success", "Success"),
    )
    id = models.CharField(default=uuid.uuid4, max_length=50, primary_key=True)
    member = models.ForeignKey(Member, on_delete=models.SET_NULL, null=True, related_name="activity")
    team = models.ForeignKey(Team, on_delete=models.SET_NULL, null=True, related_name="all_activity")
    create_time = models.DateTimeField(null=True)
    status = models.CharField(max_length=30, choices=ACTIVITY_STATUS)
    description = models.TextField(blank=True, null=True)


def current_time():
    return datetime.now(timezone.utc)

