from django.urls import path
from webportal import views


urlpatterns = [
    path("", views.index, name="index"),
]
