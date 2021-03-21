import uuid
from datetime import datetime, timezone

from django.views import View
from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import QueryDict

from utils.mixins import ResponseMixin
from utils.handlers import EmailHandler
from .models import Order, Transaction, Customer, Promo


class TransactionUtility(LoginRequiredMixin, View, ResponseMixin):

    def post(self, request):
        transaction_id = request.POST.get("transaction_id")
        try:
            transaction = Transaction.objects.get(id=transaction_id)
            if (datetime.now(timezone.utc) - transaction.last_otp_generation_time).total_seconds() > 120:
                otp = uuid.uuid4().hex.upper()[0:6]
                transaction.otp = otp
                transaction.last_otp_generation_time = datetime.now(timezone.utc)
                transaction.save()
                msg = f"Hi {transaction.patron.user.first_name}," \
                      f"\nPlease copy paste the OTP below to authorize the transaction " \
                      f"of ${transaction.amount} to {transaction.recipient.user.first_name} " \
                      f"#{transaction.recipient.tag}\n\n" \
                      f"{otp}\n\n" \
                      f"Please do not share this otp with anyone\n" \
                      f"Thank you!\n~Novanodes"
                EmailHandler.send_email(transaction.patron.user.email,
                                        "OTP for transaction",
                                        msg=msg)
                return self.json_response_200()
            else:
                return self.json_response_503()
        except Transaction.DoesNotExist:
            return self.json_response_500()

    def put(self, request):
        data = QueryDict(request.body)
        transaction_id = data.get("transaction_id")
        try:
            transaction = Transaction.objects.get(id=transaction_id, status="fa-clock text-warning")
            return render(request, "dashboard/refresh_pages/transaction_refresh.html", {"recipient": transaction.recipient,
                                                                          "transaction_id": transaction.id},
                          status=200)
        except Transaction.DoesNotExist:
            return self.json_response_500()


class TransactionView(LoginRequiredMixin, View, ResponseMixin):

    def get(self, request):
        return render(request, "dashboard/transactions.html")

    def post(self, request):
        if not request.user.customer.verified:
            return self.json_response_501()
        account_no = request.POST.get("account_no")
        if int(account_no) == request.user.customer.id:
            return self.json_response_405()
        amount = float(request.POST.get("amount"))
        msg = request.POST.get("msg")
        if amount < 1:
            return self.json_response_403()
        if amount > request.user.customer.credits:
            return self.json_response_503()
        try:
            recipient = Customer.objects.get(id=account_no)
            otp = uuid.uuid4().hex.upper()[0:6]
            transaction = Transaction.objects.create(
                patron=request.user.customer,
                recipient=recipient,
                amount=amount,
                status="fa-clock text-warning",
                msg=msg,
                otp=otp,
                last_otp_generation_time=datetime.now(timezone.utc)
            )
            msg = f"Hi {request.user.first_name},\nPlease copy paste the OTP below to authorize the transaction " \
                  f"of ${amount} to {recipient.user.first_name} #{recipient.user.customer.tag}\n\n" \
                  f"{otp}\n\n" \
                  f"Please do not share this otp with anyone\n" \
                  f"Thank you!\n~Novanodes"
            EmailHandler.send_email(request.user.email,
                                    "OTP for transaction",
                                    msg=msg)
            return render(request, "dashboard/refresh_pages/transaction_refresh.html", {"recipient": recipient,
                                                                          "transaction_id": transaction.id},
                          status=200)
        except Customer.DoesNotExist:
            return self.json_response_404()

    def put(self, request):
        data = QueryDict(request.body)
        transaction_id = data.get("transaction_id")
        otp = data.get("otp")
        try:
            transaction = Transaction.objects.get(id=transaction_id, status="fa-clock text-warning")
            if otp == transaction.otp:
                if transaction.amount > request.user.customer.credits:
                    transaction.status = "fa-times-circle text-danger"
                    transaction.save()
                    return self.json_response_503()
                else:
                    request.user.customer.credits -= transaction.amount
                    transaction.recipient.credits += transaction.amount
                    transaction.status = "fa-check-circle text-success"
                    transaction.save()
                    request.user.customer.save()
                    transaction.recipient.save()
                    return render(request, "dashboard/refresh_pages/pending_transactions.html", status=200)
            else:
                transaction.status = "fa-times-circle text-danger"
                transaction.failure_message = "OTP mismatch"
                transaction.save()
                return self.json_response_400()
        except Transaction.DoesNotExist:
            return self.json_response_500()

    def delete(self, request):
        transaction_id = request.GET.get("transaction_id")
        try:
            transaction = Transaction.objects.get(id=transaction_id, status="fa-clock text-warning")
            transaction.status = "fa-ban text-danger"
            transaction.save()
            return render(request, "dashboard/refresh_pages/pending_transactions.html", status=200)
        except Transaction.DoesNotExist:
            return self.json_response_500()


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
