from django.shortcuts import render
from django.views import View

# Create your views here.


def index(request):
    return render(request, "index.html")


def about(request):
    return render(request, "about.html")


def privacy(request):
    return render(request, "privacy-policy.html")


def terms(request):
    return render(request, "terms-condition.html")


class ContactView(View):

    def get(self, request, name=None):
        if name is None:
            return render(request, "index.html")
        else:
            return render(request, f"{name}.html")
