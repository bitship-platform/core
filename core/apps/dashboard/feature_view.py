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


class ExchangeView(LoginRequiredMixin, View, ResponseMixin):

    def post(self, request):
        coins = int(request.POST.get("coins"))
        if coins > request.user.customer.coins:
            return self.json_response_503()
        customer = request.user.customer
        customer.coins -= coins
        customer.credits += coins * 0.12
        customer.coins_redeemed += coins
        customer.save()
        Order.objects.create(customer=customer,
                             transaction_amount=format(coins * 0.12, '.2f'),
                             credit=True,
                             create_time=datetime.now(timezone.utc),
                             update_time=datetime.now(timezone.utc),
                             service="Coin Exchange",
                             status="fa-check-circle text-success")
        return render(request, "dashboard/refresh_pages/stats_refresh.html", status=200)

