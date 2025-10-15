from django.urls import re_path

from . import views

app_name = "iiif"
urlpatterns = [
    re_path(r"(?P<path>.*)", views.IIIFProxyView.as_view()),
]
