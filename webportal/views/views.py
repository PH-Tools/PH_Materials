from django.core.handlers.wsgi import WSGIRequest
from django.http import HttpResponse
from django.shortcuts import render


# ---------------------------------------------------------------------------------------
def index(request: WSGIRequest) -> HttpResponse:
    return render(request, "webportal/index.html")
