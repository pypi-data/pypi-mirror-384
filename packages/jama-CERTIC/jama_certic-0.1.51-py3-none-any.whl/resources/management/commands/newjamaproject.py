from django.core.management.base import BaseCommand, CommandError
from resources.models import (
    Project,
    Role,
    Permission,
    ProjectAccess,
    APIKey,
    MetadataSet,
    Metadata,
)
from django.utils.text import slugify
from django.contrib.auth.models import User
import secrets
import string


DC_METAS = [
    ["title", "A name given to the resource"],
    ["creator", "An entity primarily responsible for making the resource."],
    ["subject", "The topic of the resource."],
    ["description", "An account of the resource."],
    ["publisher", "An entity responsible for making the resource available."],
    ["contributor", "An entity responsible for making contributions to the resource."],
    [
        "date",
        "A point or period of time associated with an event in the lifecycle of the resource.",
    ],
    ["type", "The nature or genre of the resource."],
    ["format", "The file format, physical medium, or dimensions of the resource."],
    ["identifier", "An unambiguous reference to the resource within a given context."],
    ["source", "A related resource from which the described resource is derived."],
    ["language", "A language of the resource."],
    ["relation", "A related resource."],
    [
        "coverage",
        "The spatial or temporal topic of the resource, the spatial applicability of the resource, or the jurisdiction under which the resource is relevant.",
    ],
    ["rights", "Information about rights held in and over the resource."],
    ["audience", "A class of entity for whom the resource is intended or useful."],
    [
        "provenance",
        "A statement of any changes in ownership and custody of the resource since its creation that are significant for its authenticity, integrity, and interpretation.",
    ],
    [
        "rightsholder",
        "A person or organization owning or managing rights over the resource.",
    ],
]


DC_ATLAS_METAS_EXTENSION = [
    ["atlas_status", "statut de publication"],
    ["atlas_topic", "thématique"],
]


def add_dc_metas(project: Project, add_atlas_extras: bool = False):
    dc_set, _ = MetadataSet.objects.get_or_create(title="Dublin_Core", project=project)
    rank = 1
    for m in DC_METAS:
        meta, _ = Metadata.objects.get_or_create(
            title=m[0], set_id=dc_set.pk, project=project, rank=rank
        )
        rank = rank + 1
    if add_atlas_extras:
        for m in DC_ATLAS_METAS_EXTENSION:
            meta, _ = Metadata.objects.get_or_create(
                title=m[0], set_id=dc_set.pk, project=project, rank=rank
            )
            rank = rank + 1
    return dc_set


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("project_label", type=str)
        parser.add_argument("--atlas_metas", action="store_true")

    def handle(self, *args, **options):
        project_label = options.get("project_label")
        add_atlas_metas = options.get("atlas_metas")
        project = Project.objects.filter(label__iexact=project_label).first()
        if project:
            raise CommandError("Le projet existe déjà.")
        project_admin_username = slugify(f"admin_{project_label.replace(' ', '_')}")
        project = Project.objects.create(label=project_label)
        admin_user, _ = User.objects.get_or_create(username=project_admin_username)
        admin_role, _ = Role.objects.get_or_create(label="admin", project=project)
        for permission in Permission.objects.all():
            admin_role.permissions.add(permission)
        ProjectAccess.objects.get_or_create(
            project=project, role=admin_role, user=admin_user
        )
        key, _ = APIKey.objects.get_or_create(
            user=admin_user,
            key="".join(
                secrets.choice(string.ascii_letters + string.digits) for _ in range(32)
            ),
        )
        key.active = True
        key.save()
        dc_set = add_dc_metas(project, add_atlas_metas)
        # create root collection
        project.root_collection
        print(
            f'Projet "{project_label}" (id {project.pk}) créé avec le compte administrateur "{admin_user.username}" et la clef d\'API "{key.key}". ID de metas Dublin Core: {dc_set.pk}'
        )
