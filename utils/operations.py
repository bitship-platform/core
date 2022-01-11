import os
import json
import shutil
import tarfile
from zipfile import ZipFile
from datetime import datetime

from django.conf import settings
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.utils.timezone import make_aware
from django.db.models.signals import post_save, post_delete

from utils.handlers import BPDAPIHandler
from core.apps.dashboard.models import Customer, Address, Folder, App, File, Setting

bpd_api = BPDAPIHandler(token=settings.BPD_SECRET)

DISCORD_EPOCH = 1420070400000


def discord_id_to_time(discord_id):
    return datetime.utcfromtimestamp(((discord_id >> 22)+DISCORD_EPOCH)/1000.)


def make_tarfile(output_filename, source_dir):
    with tarfile.open(f"media/{output_filename}", "w:gz") as tar:
        tar.add(source_dir, arcname=os.path.basename(source_dir))


def create_backup(app, path):
    system_files = ["Procfile", "app.json", "runtime.txt"]
    with ZipFile(os.path.join(settings.MEDIA_ROOT, f"{app.unique_id}_backup.zip"), "w") as backup:
        for root, dirs, files in os.walk(path):
            for file in files:
                if file not in system_files:
                    backup.write(os.path.join(root, file),
                                 os.path.relpath(os.path.join(root, file),
                                                 os.path.join(path, '..')))


def set_system_files(app: App, file_name, content):
    path = os.path.join(settings.MEDIA_ROOT, f"{app.owner.id}/{app.name}/")
    with open(path+file_name, "w") as file:
        file.write(content)


def remove_dir_from_storage(path):
    try:
        shutil.rmtree(os.path.join(settings.MEDIA_ROOT, path))
    except Exception as E:
        pass


def remove_file_from_storage(path):
    try:
        os.remove(os.path.join(settings.MEDIA_ROOT, path))
    except Exception as E:
        pass


def create_customer(user_json: dict, password: str):
    """
    creates new user if the user is not in the database.
    :param user_json: discord oauth2 json data
    :param password: hashed user password
    :return: user: Customer
    """
    user_id = user_json["id"]
    user = User.objects.create_user(is_staff=True,
                                    username=user_id,
                                    password=password,
                                    email=user_json["email"],
                                    first_name=user_json["username"]
                                    )
    customer = Customer.objects.create(id=user_id,
                                       user=user,
                                       credits=0,
                                       avatar=user_json["avatar"],
                                       tag=user_json["discriminator"],
                                       creation_date=make_aware(discord_id_to_time(int(user_id))))
    Address.objects.create(customer=customer)
    Setting.objects.create(customer=customer)
    return customer


def update_customer(user_json: dict):
    user_id = user_json["id"]
    try:
        user = Customer.objects.get(id=user_id)
        user.avatar = user_json["avatar"]
        user.tag = str(user_json["discriminator"])
        user.user.first_name = user_json["username"]
        user.save()

    except Exception as e:
        print("Exception", e)
        # TODO:  attach webhook


@receiver(post_save, sender=App)
def create_app_folder(sender, instance, created, **kwargs):
    if created:
        Folder.objects.create(owner=instance.owner, name=instance.name, app=instance)


@receiver(post_save, sender=File)
def update_folder_size_on_create(sender, instance, created, **kwargs):
    if created:
        folder = instance.folder
        while folder.folder:
            folder.size += instance.size
            folder.save()
            folder = folder.folder


@receiver(post_delete, sender=File)
def update_folder_size_on_delete(sender, instance, **kwargs):
    folder = instance.folder
    while folder.folder:
        folder.size -= instance.size
        folder.save()
        folder = folder.folder
    if instance.item:
        if os.path.isfile(instance.item.path):
            os.remove(instance.item.path)


@receiver(post_delete, sender=App)
def terminate_app_on_delete(sender, instance, **kwargs):
    bpd_api.terminate(instance.unique_id)
