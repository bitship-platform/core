import requests
from django.conf import settings


class Oauth(object):
    client_id = settings.OAUTH_CLIENT_ID
    client_secret = settings.OAUTH_CLIENT_SECRET
    discord_token_url = "https://discord.com/api/oauth2/token"
    discord_api_url = "https://discord.com/api"

    def __init__(self, redirect_uri,
                 scope="identify%20email"):
        self.redirect_uri = redirect_uri
        self.scope = scope
        self.discord_login_url = "https://discord.com/api/oauth2/authorize?client_id={}" \
                                 "&redirect_uri={}&response_type=code&scope={}".format(self.client_id,
                                                                                       self.redirect_uri,
                                                                                       self.scope)

    def get_access_token(self, code):
        payload = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': self.redirect_uri,
            'scope': self.scope
        }

        headers = {
         'Content-Type': 'application/x-www-form-urlencoded'
        }

        access_token = requests.post(url=self.discord_token_url, data=payload, headers=headers)
        json = access_token.json()
        return json.get("access_token")

    @staticmethod
    def get(access_token, endpoint):

        headers = {
            "Authorization": "Bearer {}".format(access_token)
        }
        response_object = requests.get(url=endpoint, headers=headers)
        return response_object.json()

    def get_user_json(self, access_token):
        url = self.discord_api_url + '/users/@me'
        return self.get(access_token, endpoint=url)

    def get_guild_info_json(self, access_token):
        url = self.discord_api_url + '/users/@me/guilds'
        return self.get(access_token, endpoint=url)
