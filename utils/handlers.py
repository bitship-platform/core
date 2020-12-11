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
