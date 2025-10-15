from django.urls import path, include
from jama import settings
from . import views
import logging
from debug_toolbar.toolbar import debug_toolbar_urls

request_logger = logging.getLogger("django.request")
request_logger.setLevel(logging.ERROR)

handler404 = "jama.views.handler404"


urlpatterns = [
    path(settings.JAMA_URL_BASE_PATH + "", views.homepage),
    path(settings.JAMA_URL_BASE_PATH + "rpc/", include("rpc.urls")),
    path(settings.JAMA_URL_BASE_PATH + "resources/", include("resources.urls")),
    path(settings.JAMA_URL_BASE_PATH + "status", views.status),
    # path(settings.JAMA_URL_BASE_PATH + "browse/", include("nui.urls", namespace="nui")),
    path(settings.JAMA_URL_BASE_PATH + "iiif/", include("iiif.urls", namespace="iiif")),
] + debug_toolbar_urls()


if settings.JAMA_USE_ARK:
    urlpatterns.append(
        path(
            settings.JAMA_URL_BASE_PATH + "ark/resource/<int:resource_id>/",
            views.ark_resource,
            name="ark_resource",
        )
    )
    urlpatterns.append(
        path(
            settings.JAMA_URL_BASE_PATH + "ark/collection/<int:collection_id>/",
            views.ark_collection,
            name="ark_collection",
        )
    )


if settings.JAMA_USE_MODSHIB:
    urlpatterns.append(
        path(
            settings.JAMA_URL_BASE_PATH + "accounts/",
            include("django.contrib.auth.urls"),
        )
    )
    urlpatterns.append(
        path(settings.JAMA_URL_BASE_PATH + "modshib/", include("modshib.urls"))
    )


for app in settings.AUTO_REGISTER_APPS:
    module = __import__(app)
    # does app have urls ?
    endpoint = getattr(module, "endpoint", None)
    if endpoint and isinstance(endpoint, str):
        urlpatterns.append(
            path(
                settings.JAMA_URL_BASE_PATH + endpoint,
                include("{}.urls".format(app)),
            )
        )
