from django.shortcuts import render
from django.views import View
from utils.handlers import hook
from django.conf import settings


class DynamicView(View):
    template_name = "index-3.html"

    def get(self, request):
        return render(request, self.template_name)


class ContactView(View):
    template_name = "contact.html"
    params = ('name', 'email', 'discord', 'msg_subject', 'message')

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        data = "".join(f"**{param}**: `{request.POST[param]}`\n"
                       for param in request.POST if param != "csrfmiddlewaretoken")
        embed = {"title": "Query submission",
                 "description": data,
                 "color": 0xFF7900,
                 "footer": {
                     "text": "powered by Novanodes"
                 }
                 }
        hook.send_embed(embed)
        return render(request, self.template_name)
