import json

import requests


class WebhookHandler:

    headers = {'Content-Type': 'application/json'}
    resp = None

    def __init__(self, webhook_id, secret):
        self.webhook_id = webhook_id
        self.secret = secret
        self.url = "https://discordapp.com/api/webhooks/{}/{}".format(self.webhook_id, self.secret)

    def _send_to_webhook(self, payload):
        payload = json.dumps(payload)
        try:
            self.resp = requests.post(url=self.url, headers=self.headers, data=payload)
        except Exception:
            pass

    def send_embed(self, payload: dict):
        payload = {"embeds": [payload]}
        self._send_to_webhook(payload)

    def send_message(self, message: str):
        payload = {"content": message}
        self._send_to_webhook(payload)


class AlertHandler:
    _type: str
    bs_class: str

    def __init__(self, atype, msg):
        self.atype = atype
        self.msg = msg

    @property
    def atype(self):
        return self._type

    @atype.setter
    def atype(self, value):
        self._type = value
        if value == "Error":
            self.bs_class = "alert-danger"
        elif value == "Success":
            self.bs_class = "alert-success"


class PaypalHandler:
    url = "https://api-m.sandbox.paypal.com/"
    headers = {"Accept": "application/json"}

    def __init__(self, client_id, client_secret):
        self.client_id = client_id
        self.client_secret = client_secret

    def _get_access_token(self):
        data = {"grant_type": "client_credentials"}
        self.headers["Accept-Language"] = "en_US"
        r = requests.post(self.url + 'v1/oauth2/token',
                          auth=(self.client_id, self.client_secret),
                          headers=self.headers, data=data).json()
        access_token = r.get('access_token')
        return access_token

    def get_order_details(self, order_id):
        self.headers["Authorization"] = f"Bearer {self._get_access_token()}"
        resp = requests.get(self.url + f"v2/checkout/orders/{order_id}", headers=self.headers).json()
        return resp
