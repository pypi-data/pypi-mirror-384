from django.core.management.base import BaseCommand
from resources.models import (
    FileExtension,
    FileType,
    MetadataSet,
    Metadata,
    Permission,
    Project,
)
import json
import csv
import pathlib

IIIF_SUPPORT = [
    "application/pdf",
    "image/png",
    "image/jpg",
    "image/jpeg",
    "image/bmp",
    "image/gif",
    "image/tiff",
]


def set_base_permissions():
    obj_types = [
        "collection",
        "resource",
        "metadata",
        "metadataset",
        "file",
        "tag",
        "role",
        "permission",
        "project",
    ]
    permissions = ["create", "read", "update", "delete"]
    for obj_type in obj_types:
        for permission in permissions:
            Permission.objects.get_or_create(label="{}.{}".format(obj_type, permission))
    Permission.objects.get_or_create(label="file.download_source")
    Permission.objects.get_or_create(label="file.upload")


def set_file_types():
    with open(
        "{}/mimes.json".format(pathlib.Path(__file__).parent.absolute()), "r"
    ) as f:
        data = json.load(f)
        for key in data:
            if "extensions" in data[key]:
                file_type, created = FileType.objects.get_or_create(mime=key, title=key)
                for extension in data[key]["extensions"]:
                    extension, created = FileExtension.objects.get_or_create(
                        label=extension
                    )
                    file_type.extensions.add(extension)
    for mime in IIIF_SUPPORT:
        try:
            file_type = FileType.objects.get(mime=mime)
            file_type.serve_with_iiif = True
            file_type.save()
        except FileType.DoesNotExist:
            pass


# deprecate ?
def set_basic_vocabularies_metas(project: Project):
    metadatasets = {}
    with open(
        "{}/vocabulary.csv".format(pathlib.Path(__file__).parent.absolute()), "r"
    ) as f:
        reader = csv.reader(f)
        next(reader)
        for row in reader:
            metadatasets[row[0]], created = MetadataSet.objects.get_or_create(
                title=row[4], project=project
            )
    metadatas = {}
    with open(
        "{}/property.csv".format(pathlib.Path(__file__).parent.absolute()), "r"
    ) as f:
        reader = csv.reader(f)
        next(reader)
        for row in reader:
            metadatas[row[0]], created = Metadata.objects.get_or_create(
                title=row[3],
                set_id=metadatasets[row[2]].pk,
                project=project,
            )


def load_fixtures(*args):
    set_base_permissions()
    set_file_types()


class Command(BaseCommand):
    def handle(self, *args, **options):
        load_fixtures()
