from django.urls import path

from . import views

urlpatterns = [
    path(
        "thumb/<str:sha256>/rotate/<str:angle>/scale/<str:scale>/crop/<str:crop>",
        views.thumb,
        name="picthumb",
    ),
    path(
        "simple_thumb/<str:sha256>/<int:size>", views.simple_thumb, name="simplethumb"
    ),
]
