from django.http import HttpRequest, HttpResponse, HttpResponseServerError

from .health_check import health_check as hc


def health_check(request: HttpRequest) -> HttpResponse:
    result = hc.check_all()
    if result:
        return HttpResponse("OK")
    return HttpResponseServerError("ERROR")
