from django.shortcuts import render
from django.views import View

# Create your views here.


class DynamicView(View):
    template_name = "index.html"

    def get(self, request):
        return render(request, self.template_name)


class ContactView(View):
    template_name = "contact.html"

    def get(self, request):
        return render(request, self.template_name)
