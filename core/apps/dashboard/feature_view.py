from datetime import datetime, timezone

from django.views import View
from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin

from utils.mixins import ResponseMixin
from .models import Order, Promo


class PromoCodeView(LoginRequiredMixin, View, ResponseMixin):

    def post(self, request):
        code = request.POST.get("promo_code")
        try:
            promo_code = Promo.objects.get(code=code)
            customer = request.user.customer
            if promo_code.offer not in customer.applied_offers.all():
                if not promo_code.expired:
                    if not promo_code.offer.expired:
                        customer.credits += promo_code.offer.credit_reward
                        customer.coins += promo_code.offer.coin_reward
                        customer.applied_offers.add(promo_code.offer)
                        customer.save()
                        return render(request, "dashboard/refresh_pages/stats_refresh.html", status=200)
                    return self.json_response_403()
                return self.json_response_403()
            return self.json_response_503()
        except Promo.DoesNotExist:
            return self.json_response_404()

