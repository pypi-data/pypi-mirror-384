from django.http import HttpResponse, HttpRequest
from django.shortcuts import render, get_object_or_404, redirect
from jama import settings
from django.contrib.auth.models import User
from resources.models import Resource, Collection
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse


def merge_query_string_to_url(url: str, qs: str) -> str:
    # Parse both URLs
    parsed1 = urlparse(url)

    # Parse query parameters
    query1 = parse_qs(parsed1.query)
    query2 = parse_qs(qs)

    # Merge the query parameters
    merged_query = query1.copy()
    for k, v in query2.items():
        if k in merged_query:
            merged_query[k].extend(v)
        else:
            merged_query[k] = v

    # Construct the new query string
    merged_query_str = urlencode(merged_query, doseq=True)

    # Create a new URL using components from url1 and the merged query
    merged_url = urlunparse(
        (
            parsed1.scheme,
            parsed1.netloc,
            parsed1.path,
            parsed1.params,
            merged_query_str,
            parsed1.fragment,
        )
    )

    return merged_url


BASE_PATH = "/" + settings.JAMA_URL_BASE_PATH


def handler404(request, *args, **argv):
    return HttpResponse("", status=404)


def homepage(request: HttpRequest) -> HttpResponse:
    if settings.JAMA_ROOT_URL_REDIRECT:
        return redirect(settings.JAMA_ROOT_URL_REDIRECT)
    return render(request, "homepage.html", {"BASE_PATH": BASE_PATH})


def status(request: HttpRequest) -> HttpResponse:
    # testing database connection
    try:
        User.objects.first()
    except:  # noqa: E722
        return HttpResponse("ko")
    return HttpResponse("ok")


def ark_resource(request: HttpRequest, resource_id: int) -> HttpResponse:
    resource = get_object_or_404(Resource, pk=resource_id, deleted_at__isnull=True)
    if resource.ptr_project.ark_redirect:
        location = (
            resource.ptr_project.ark_redirect.replace("[CLASS]", "resource")
            .replace("[ARK]", str(resource.ark))
            .replace("[PK]", str(resource.pk))
        )
        if request.META["QUERY_STRING"]:
            location = merge_query_string_to_url(location, request.META["QUERY_STRING"])
        return redirect(location)
    return HttpResponse("Jama Resource ARK location placeholder")


def ark_collection(request: HttpRequest, collection_id: int) -> HttpResponse:
    collection = get_object_or_404(
        Collection, pk=collection_id, deleted_at__isnull=True
    )
    if collection.project.ark_redirect:
        location = (
            collection.project.ark_redirect.replace("[CLASS]", "collection")
            .replace("[ARK]", str(collection.ark))
            .replace("[PK]", str(collection.pk))
        )
        if request.META["QUERY_STRING"]:
            location = merge_query_string_to_url(location, request.META["QUERY_STRING"])
        return redirect(location)
    return HttpResponse("Jama Collection ARK location placeholder")
