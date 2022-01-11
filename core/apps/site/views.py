from django.shortcuts import render
from django.views import View


class DynamicView(View):
    template_name = "index-3.html"

    def get(self, request):
        return render(request, self.template_name)


