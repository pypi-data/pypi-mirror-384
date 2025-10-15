from django.urls import path

from . import views

urlpatterns = [
    path("", views.rpc, name="rpc"),
    path("upload/", views.upload_partial, name="upload"),
    path("upload/partial/", views.upload_partial, name="upload_partial"),
    path("download/<int:file_id>", views.force_download, name="force_download"),
    path(
        "download_public/<str:file_hash>",
        views.force_download_public,
        name="force_download_public",
    ),
    path(
        "serve/<str:file_hash>",
        views.serve_file_public,
        name="serve_file_public",
    ),
    path(
        "metas/download/collection_<int:collection_id>.xlsx",
        views.download_metas_xls,
        name="metas_download",
    ),
    path(
        "metas/upload/",
        views.upload_metas_xls,
        name="metas_upload",
    ),
]
