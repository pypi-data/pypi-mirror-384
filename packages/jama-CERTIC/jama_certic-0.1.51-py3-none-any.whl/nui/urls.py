from django.urls import path

from . import views

app_name = "nui"
urlpatterns = [
    path("", views.index, name="index"),
    path("collection/<int:collection_id>", views.collection, name="collection"),
    path(
        "collection/<int:collection_id>/resource/<int:resource_id>",
        views.resource,
        name="resource",
    ),
    path("search", views.search, name="search"),
    # path("test", views.test),
]
