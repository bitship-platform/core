from django.http import HttpResponse, JsonResponse
from django.shortcuts import render

class Response:
    code_204 = {"response": "204", "message": "No Content"}
    code_400 = {"response": "400", "message": "Bad Gateway"}
    code_401 = {"response": "401", "message": "Unauthorized"}


class ResponseMixin(object):

    @staticmethod
    def json_response_204():
        return JsonResponse({"response": "Not Content"}, status=204)

    @staticmethod
    def json_response_400():
        return JsonResponse({"response": "Bad Request"}, status=400)

    @staticmethod
    def json_response_401():
        return JsonResponse({"response": "Unauthorized"}, status=401)

    @staticmethod
    def json_response_404():
        return JsonResponse({"response": "Not Found"}, status=404)

    @staticmethod
    def json_response_405():
        return JsonResponse({"response": "Method Not Allowed"}, status=405)

    @staticmethod
    def json_response_500():
        return JsonResponse({"response": "Internal Server Error"}, status=500)

    @staticmethod
    def json_response_501():
        return JsonResponse({"response": "Not Implemented"}, status=501)

    @staticmethod
    def json_response_502():
        return JsonResponse({"response": "Bad Gateway"}, status=502)

    @staticmethod
    def json_response_503():
        return JsonResponse({"response": "Internal Server Error"}, status=503)

    @staticmethod
    def json_response_504():
        return JsonResponse({"response": "Gateway Timeout"}, status=504)

    @staticmethod
    def http_responce_400(request):
        return render(request, Response.code_400, status=400)

    @staticmethod
    def http_responce_401(request):
        return render(request, Response.code_401, status=401)

    @staticmethod
    def http_responce_403():
        return HttpResponse("<h1>Forbidden (403)</h1>", status=403)

    @staticmethod
    def http_responce_404():
        return HttpResponse("<h1>Page not found (404)</h1>", status=404)

    @staticmethod
    def http_responce_405():
        return HttpResponse("<h1>Method Not Allowed (405)", status=405)
