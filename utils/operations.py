# from django.contrib.auth.models import User
#
#
# def user_signup(user_json: dict, password: str):
#     user = User.objects.create_user(username=user_json["username"],
#                                     password=password,
#                                     is_staff=True,
#                                     first_name=user_json["username"],
#                                     email=user_json["email"])