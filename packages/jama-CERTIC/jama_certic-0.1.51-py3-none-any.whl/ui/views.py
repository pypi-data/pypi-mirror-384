from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from rpc import methods as jama


@login_required
def index(request: HttpRequest) -> HttpResponse:
    accesses = jama.projects_user_permissions(request.user)
    for access in accesses:
        access["project_stats"] = jama.project_stats(
            request.user, access["project"]["id"]
        )
    return render(
        request,
        "ui/index.html",
        {"accesses": accesses, "choose_project_page": True},
    )
