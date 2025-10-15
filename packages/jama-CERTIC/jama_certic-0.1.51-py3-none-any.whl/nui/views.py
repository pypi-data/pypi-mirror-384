from typing import List
from django.shortcuts import render, get_object_or_404
from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse, Http404
from resources.models import (
    ProjectAccess,
    Collection,
    Project,
    Resource,
    Metadata,
    MetadataResourceValue,
)
from django.core.paginator import Paginator, EmptyPage
from django.views.decorators.cache import never_cache
from rpc.methods import _user_has_permission as user_has_permission
from django.contrib.auth.models import User
from rpc.const import PERM_RESOURCE_UPDATE

RESOURCES_PAGES_SIZE = 500


def editable_metadatas(project: Project) -> List[Metadata]:
    return (
        Metadata.objects.filter(project=project)
        .exclude(set__title__in=["ExifTool", "OCR"])
        .order_by("set", "title")
        .select_related("set")
    )


def user_has_project_access(user: User, project: Project) -> bool:
    if not ProjectAccess.objects.filter(project=project, user=user).first():
        raise PermissionDenied()


@login_required
@never_cache
def index(request: HttpRequest) -> HttpResponse:
    return render(
        request,
        "nui/index.html",
        {"accesses": ProjectAccess.objects.filter(user=request.user).iterator()},
    )


@login_required
@never_cache
def collection(request: HttpRequest, collection_id: int) -> HttpResponse:
    collection_instance: Collection = get_object_or_404(Collection, pk=collection_id)
    project_instance = collection_instance.project
    user_has_project_access(request.user, project_instance)
    resources = (
        collection_instance.resources.filter(deleted_at__isnull=True)
        .order_by("collectionmembership__rank", "title")
        .select_related("file")
    )
    resources_paginator = Paginator(resources, RESOURCES_PAGES_SIZE)
    try:
        page_number = int(request.GET.get("page", 1))
    except ValueError:
        page_number = 1
    try:
        resources_page = resources_paginator.page(page_number)
    except EmptyPage:
        resources_page = None
    return render(
        request,
        "nui/collection.html",
        {
            "collection": collection_instance,
            "project": project_instance,
            "resources_page": resources_page,
            "page_number": page_number,
        },
    )


def _fetch_resource(resource_id: int) -> Resource:
    return (
        Resource.objects.filter(pk=resource_id, deleted_at__isnull=True)
        .prefetch_related(
            "metadataresourcevalue_set",
            "metadataresourcevalue_set__metadata",
            "metadataresourcevalue_set__metadata__set",
        )
        .first()
    )


@login_required
@never_cache
def resource(
    request: HttpRequest, collection_id: int, resource_id: int
) -> HttpResponse:
    collection_instance: Collection = get_object_or_404(
        Collection, pk=collection_id, deleted_at__isnull=True
    )
    transient_message = ""
    resource_instance = _fetch_resource(resource_id)
    if not resource_instance:
        raise Http404()
    project_instance = resource_instance.ptr_project
    user_has_project_access(request.user, project_instance)
    user_has_update_permission = user_has_permission(
        request.user, project_instance, PERM_RESOURCE_UPDATE
    )
    if request.method == "POST" and user_has_update_permission:
        for key in request.POST.keys():
            new_title = request.POST.get("resource_title", "").strip()
            if new_title:
                resource_instance.title = new_title
                resource_instance.save()
            if "_" in key:
                parts = key.split("_")
                try:
                    int(parts[1])
                except ValueError:
                    continue
                if parts[0] == "addvalue":
                    metadata = Metadata.objects.get(
                        pk=parts[1], project=project_instance
                    )
                    for val in request.POST.getlist(key):
                        MetadataResourceValue.objects.get_or_create(
                            resource=resource_instance,
                            metadata=metadata,
                            value=val.strip(),
                        )
                if parts[0] == "changevalue":
                    new_val = request.POST.get(key).strip()
                    metaval = MetadataResourceValue.objects.filter(
                        pk=parts[1], resource=resource_instance
                    ).first()
                    if metaval and new_val != metaval.value:
                        metaval.value = new_val
                        metaval.save()
                if parts[0] == "deletevalue":
                    metaval = MetadataResourceValue.objects.get(
                        pk=parts[1], resource=resource_instance
                    )
                    metaval.delete()
        resource_instance = _fetch_resource(resource_id)  # reload metas
        transient_message = "Resource enregistrée"

    previous_resource = None
    next_resource = None
    ids_list = list(
        collection_instance.resources.filter(deleted_at__isnull=True)
        .order_by("collectionmembership__rank", "title")
        .values_list("id", flat=True)
    )
    for i in range(len(ids_list)):
        if ids_list[i] == resource_instance.pk:
            if ids_list[i - 1] != ids_list[-1]:
                previous_resource = Resource.objects.get(pk=ids_list[i - 1])
            if i < len(ids_list) - 1:
                next_resource = Resource.objects.get(pk=ids_list[i + 1])

    return render(
        request,
        "nui/resource.html",
        {
            "resource": resource_instance,
            "collection": collection_instance,
            "project": project_instance,
            "previous_resource": previous_resource,
            "next_resource": next_resource,
            "editable_metadatas": editable_metadatas(project_instance),
            "user_has_update_permission": user_has_update_permission,
            "transient_message": transient_message,
        },
    )


def search(request: HttpRequest) -> HttpResponse:
    collection_search = Collection.objects.filter(
        title__icontains=request.GET.get("q")
    ).order_by("title")
    resource_search = Resource.objects.filter(
        title__icontains=request.GET.get("q")
    ).order_by("title")
    return render(
        request,
        "nui/search.html",
        {"collection_search": collection_search, "resource_search": resource_search},
    )
