from django.core.management.base import BaseCommand, CommandError
import os
from django.contrib.auth.models import User
from typing import Iterator
from rpc.methods import add_collection_from_path, add_resource_to_collection
from functools import lru_cache
from resources.helpers import handle_local_file
from resources.models import Project, FileExtension
from resources import tasks
from concurrent.futures import ThreadPoolExecutor
import multiprocessing
from pathlib import Path


@lru_cache(maxsize=None)
def cached_add_collection_from_path(*args, **kwargs):
    return add_collection_from_path(*args, **kwargs)


ALLOWED_EXTENSIONS = []

for ext in FileExtension.objects.all():
    ALLOWED_EXTENSIONS.append(".{}".format(ext.label))


def scan_dir(start_path: str, extension: str = None) -> Iterator[str]:
    for root, dirs, files in os.walk(start_path):
        for file in files:
            if extension:
                if file[(len(extension) * -1) :].lower() == extension.lower():
                    yield os.path.join(root, file)
            else:
                yield os.path.join(root, file)


def _add_file(
    file_path: str,
    project: Project,
    current_user: User,
    start_dir: str,
    delete_source: bool = False,
):
    resource_id = handle_local_file(file_path, project)
    tasks.iiif_task(resource_id)
    tasks.exif_task(resource_id)
    tasks.ocr_task(resource_id)
    collection_path = os.path.dirname(file_path)[len(start_dir) :]
    if collection_path:
        hierarchy_of_collections = cached_add_collection_from_path(
            current_user, collection_path, project.pk
        )
        collection_id = hierarchy_of_collections[-1]["id"]
        if add_resource_to_collection(current_user, resource_id, collection_id):
            if delete_source:
                Path(file_path).unlink(missing_ok=True)


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("start_dir", type=str)
        parser.add_argument("user", type=str)
        parser.add_argument("project", type=int)
        parser.add_argument("--extensions", nargs="+", type=str)
        parser.add_argument("--delete", action="store_true")

    def handle(self, *args, **options):
        if options.get("extensions"):
            allowed_extensions = options.get("extensions")
        else:
            allowed_extensions = ALLOWED_EXTENSIONS
        delete_source = options.get("delete", False)
        start_dir = options.get("start_dir")
        if not os.path.isdir(start_dir):
            raise CommandError("{} is not a directory".format(start_dir))
        try:
            project = Project.objects.get(pk=options.get("project"))
        except Project.DoesNotExist:
            raise CommandError(
                "({}) is not a known project".format(options.get("project"))
            )
        try:
            current_user = User.objects.get(username=options.get("user"))
        except User.DoesNotExist:
            raise CommandError("({}) is not a known user".format(options.get("user")))

        executor = ThreadPoolExecutor(max_workers=multiprocessing.cpu_count())

        for file_path in scan_dir(start_dir):
            _, extension = os.path.splitext(file_path)
            if extension.lower() not in allowed_extensions:
                continue
            executor.submit(
                _add_file, file_path, project, current_user, start_dir, delete_source
            )
