import uuid
from datetime import datetime, timezone
from itertools import chain

from django.db import models
from django.contrib.auth.models import User
from utils.misc import PythonAppConfig, NodeAppConfig


class Customer(models.Model):
    """
    Users signed up to the site.
    """
    id = models.BigIntegerField(primary_key=True)
    tag = models.CharField(max_length=5, default="0000")
    avatar = models.CharField(max_length=50, null=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="customer")
    credits = models.FloatField(default=0)
    verified = models.BooleanField(default=False)
    credits_spend = models.FloatField(default=0)
    coins = models.IntegerField(default=0)
    coins_redeemed = models.IntegerField(default=0)
    banned = models.BooleanField(default=False)
    applied_offers = models.ManyToManyField("Offer", blank=True)
    creation_date = models.DateTimeField(null=True, blank=True)
    joined_server = models.BooleanField(default=False)
    referrer = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, related_name="affiliate")
    affiliate_commission = models.FloatField(default=0)
    affiliate_commission_spent = models.FloatField(default=0)
    first_order_amount = models.FloatField(default=0)
    dark_mode = models.BooleanField(default=False)

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
        self.credits = 0
        self.credits_spend = 0
        self.app_set.all().delete()
        self.order.all().delete()
        self.verified = False
        self.address.reset()
        self.save()

    @property
    def earnings(self):
        return self.first_order_amount/2

    @property
    def running_apps(self):
        return len(self.app_set.filter(status__in=["bg-success", "bg-danger"]))

    @property
    def terminated_apps(self):
        return self.settings.display_terminated_apps

    @property
    def rounded_credits(self):
        return round(self.credits, 2)

    @property
    def get_orders(self):
        return self.order.all().order_by("-create_time")

    @property
    def get_transactions(self):
        result_list = list(chain(self.recipient.all(), self.patron.all()))
        return sorted(result_list, key=lambda instance: instance.time, reverse=True)

    @property
    def pending_transactions(self):
        return self.patron.filter(status="fa-clock text-warning")


class App(models.Model):
    """
    User's running applications.
    """
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
    TYPE_CHOICES = [
        (1.2, "Base"),
        (2.4, "Standard"),
        (4.99, "Premium"),
    ]
    name = models.CharField(max_length=50, default="nova-app")
    unique_id = models.UUIDField(default=uuid.uuid4, null=True)
    owner = models.ForeignKey(Customer, on_delete=models.CASCADE)
    status = models.CharField(choices=STATUS_CHOICES, default="STOPPED", max_length=20)
    stack = models.URLField(choices=STACK_CHOICES, default="Python")
    plan = models.FloatField(choices=TYPE_CHOICES)
    cpu = models.IntegerField(default=0, null=True)
    ram = models.IntegerField(default=0, null=True)
    disk = models.IntegerField(default=0, null=True)
    network = models.IntegerField(default=0, null=True)
    glacier = models.IntegerField(default=0, null=True)
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

    @property
    def running(self):
        if self.get_status_display() == "Running":
            return True
        return False

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
        if self.get_status_display() in ["Pending", "Not Started", "Stopped"]:
            return True
        return False

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
            if "python_version" and "app_json" and "main_executable" in self.config:
                return True
        elif self.node:
            if "node_version" and "app_json" and "start_script" in self.config:
                return True
        return False

    @property
    def app_stack(self):
        return self.get_stack_display()

    @property
    def app_status(self):
        return self.get_status_display()

    @property
    def app_plan(self):
        return self.get_plan_display()

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


class Address(models.Model):
    customer = models.OneToOneField(Customer, primary_key=True, on_delete=models.CASCADE)
    firstname = models.CharField(max_length=50, null=True)
    lastname = models.CharField(max_length=50, null=True)
    location = models.TextField(null=True)
    city = models.CharField(max_length=100, null=True)
    country = models.CharField(max_length=100, null=True)
    pincode = models.IntegerField(null=True)

    def reset(self):
        self.firstname = None
        self.lastname = None
        self.location = None
        self.city = None
        self.country = None
        self.pincode = None
        self.save()


class Setting(models.Model):
    customer = models.OneToOneField(Customer, primary_key=True, on_delete=models.CASCADE, related_name="settings")
    email_notification = models.BooleanField(default=False)
    app_status_alert = models.BooleanField(default=False)
    down_time_alert = models.BooleanField(default=False)
    maintenance_break_alert = models.BooleanField(default=False)
    new_offers_alert = models.BooleanField(default=False)
    display_terminated_apps = models.BooleanField(default=False)
    beta_tester = models.BooleanField(default=False)
    affiliate = models.BooleanField(default=False)


def upload_location(instance, filename):
    folder = instance.folder
    path = ""
    while folder is not None:
        if folder.name:
            path = f"/{folder.name}" + path
        folder = folder.folder
    return f"{instance.folder.owner.id}" + path + f"/{filename}"


class Referral(models.Model):
    affiliate = models.ForeignKey(Customer, on_delete=models.CASCADE)
    ip = models.CharField(max_length=50)
    creation_time = models.DateTimeField(auto_now_add=True)


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

        return f"/{self.folder.owner.id}" + path + f"/{self.name}"

    def get_size(self):
        mb_size = self.size//1000000
        if not mb_size:
            return f"{self.size/1000}kb"
        else:
            return f"{mb_size}mb"


class Order(models.Model):
    ORDER_STATUS = (
        ("fa-times-circle text-danger", "Failed"),
        ("fa-clock text-warning", "Pending"),
        ("fa-check-circle text-success", "Success"),
    )
    id = models.CharField(default=uuid.uuid4, max_length=50, primary_key=True)
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, related_name="order")
    transaction_amount = models.FloatField(default=0)
    payer_id = models.CharField(max_length=20, blank=True, null=True)
    payer_email = models.CharField(max_length=30, blank=True, null=True)
    create_time = models.DateTimeField(null=True)
    update_time = models.DateTimeField(null=True)
    status = models.CharField(max_length=30, choices=ORDER_STATUS)
    service = models.CharField(max_length=30, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    credit = models.BooleanField(default=False)


class Transaction(models.Model):
    TRANSACTION_STATUS = (
        ("fa-ban text-danger", "Canceled"),
        ("fa-times-circle text-danger", "Failed"),
        ("fa-clock text-warning", "Pending"),
        ("fa-check-circle text-success", "Success"),
    )
    id = models.UUIDField(default=uuid.uuid4, primary_key=True)
    patron = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="patron")
    recipient = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, related_name="recipient")
    time = models.DateTimeField(auto_now_add=True)
    amount = models.FloatField(default=0)
    status = models.CharField(max_length=30, choices=TRANSACTION_STATUS)
    failure_message = models.CharField(max_length=120, null=True, blank=True)
    msg = models.TextField(null=True, blank=True)
    otp = models.CharField(max_length=6, null=True, blank=True)
    last_otp_generation_time = models.DateTimeField(null=True, blank=True)


class Offer(models.Model):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True)
    name = models.CharField(max_length=30)
    description = models.TextField(blank=True, null=True)
    creation_date = models.DateTimeField(auto_now_add=True)
    expiry_date = models.DateTimeField()
    coin_reward = models.IntegerField(default=0)
    credit_reward = models.FloatField(default=0.0)

    @property
    def expired(self):
        if datetime.now(timezone.utc) > self.expiry_date:
            return True
        return False


class Promo(models.Model):
    code = models.CharField(max_length=20, primary_key=True)
    offer = models.ForeignKey(Offer, on_delete=models.CASCADE)
    expiry_date = models.DateTimeField()

    @property
    def expired(self):
        if datetime.now(timezone.utc) > self.expiry_date:
            return True
        return False


class CashoutRequest(models.Model):
    STATUS = (
        ("fa-ban text-danger", "Canceled"),
        ("fa-times-circle text-danger", "Failed"),
        ("fa-clock text-warning", "Pending"),
        ("fa-check-circle text-success", "Success"),
    )
    customer = models.ForeignKey("Customer", on_delete=models.CASCADE)
    paypal_email = models.CharField(max_length=100)
    amount = models.FloatField()
    status = models.CharField(max_length=30, choices=STATUS, default="fa-clock text-warning")
