from django.contrib.auth.models import User
from nova_dash.models import Customer, Address, Folder, App
from django.db.models.signals import post_save
from django.dispatch import receiver

def create_customer(user_json: dict, password: str):
    """
    creates new user if the user is not in the database.
    :param user_json: discord oauth2 json data
    :param password: hashed user password
    :return: user: Customer
    """
    user_id = user_json["id"]
    user = User.objects.create_user(username=user_id,
                                    password=password,
                                    is_staff=True,
                                    first_name=user_json["username"],
                                    email=user_json["email"]
                                    )
    customer = Customer.objects.create(id=user_id,
                                       user=user,
                                       credits=0,
                                       tag=user_json["discriminator"],
                                       avatar=user_json["avatar"])
    Address.objects.create(customer=customer)
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
        folder = Folder.objects.create(owner=instance.owner, name=instance.name)
        instance.folder = folder
        instance.save()
