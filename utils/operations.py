from django.contrib.auth.models import User
from nova_dash.models import Customer

def get_avatar_url(user_id, avatar_hash):
    """
    formats and returns user's avatar url
    :param user_id: discord user id
    :param avatar_hash: discord avatar hash
    :return: str: User's avatar url
    """
    return f"https://cdn.discordapp.com/avatars/{user_id}/{avatar_hash}.png"


def create_customer(user_json: dict, password: str):
    """
    creates new user if the user is not in the database.
    :param user_json: discord oauth2 json data
    :param password: hashed user password
    :return: user: Customer
    """
    user_id = user_json["id"]
    user, created = User.objects.update_or_create(username=user_id,
                                                  password=password,
                                                  is_staff=True,
                                                  first_name=user_json["username"],
                                                  email=user_json["email"]
                                                  )
    customer = Customer.objects.create(id=user_id,
                                       user=user,
                                       credits=0,
                                       avatar=get_avatar_url(user_id, user_json["avatar"]))
    return customer


