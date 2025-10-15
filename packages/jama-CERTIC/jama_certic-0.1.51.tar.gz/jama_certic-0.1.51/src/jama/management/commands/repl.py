from django.core.management.commands.shell import Command
from django.contrib.auth.models import User
from rich.console import Console
from rich.table import Table
from typing import List, Union
from resources.helpers import make_iiif, make_ocr
from django.utils.text import slugify
import secrets
import string

# from pick import pick
from resources.models import (
    Resource,
    Collection,
    Project,
    APIKey,
    ProjectAccess,
    Permission,
    File,
    ProjectProperty,
    UserTask,
    Tag,
    FileExtension,
    FileType,
    MetadataSet,
    Metadata,
    MetadataCollectionValue,
    MetadataResourceValue,
    CollectionMembership,
    Role,
)


def _console_table(title: str, headers: List["str"]) -> Table:
    table = Table(title=title)
    for header in headers:
        table.add_column(header)
    return table


def user(*args, **kwargs):
    return User.objects.get(*args, **kwargs)


def project(*args, **kwargs):
    return Project.objects.get(*args, **kwargs)


def projects(*args, **kwargs):
    table = _console_table(
        "Projects",
        [
            "pk",
            "label",
            "users",
        ],
    )

    for p in Project.objects.filter(*args, **kwargs):
        table.add_row(
            str(p.pk),
            str(p.label),
            ", ".join(
                f"{a.user.username} ({a.user.pk})"
                for a in ProjectAccess.objects.filter(project=p)
            ),
        )
    Console().print(table)


def users(*args, **kwargs):
    # option, index = pick(["some", "of", "this"], "choose...", multiselect=True)
    table = _console_table(
        "Users",
        ["pk", "username", "email", "active", "last login", "superuser", "projects"],
    )
    for u in User.objects.filter(*args, **kwargs).order_by("username"):
        table.add_row(
            str(u.pk),
            str(u.username),
            str(u.email),
            str(u.is_active),
            str(u.last_login),
            str(u.is_superuser),
            ", ".join(
                f"{a.project.label} ({a.project.pk})"
                for a in ProjectAccess.objects.filter(user=u)
            ),
        )
    Console().print(table)


def accesses():
    for a in ProjectAccess.objects.order_by("project"):
        print(a.pk, a)


def move_collection_to_project(from_collection_id: int, to_project_id: int):
    from resources.tasks import ocr_task

    from_collection_instance = Collection.objects.get(pk=from_collection_id)
    to_project_instance = Project.objects.get(pk=to_project_id)
    from_collection_instance.parent = to_project_instance.root_collection
    from_collection_instance.project = to_project_instance
    from_collection_instance.save()
    print(f"Collection({from_collection_instance.id})")
    for col in from_collection_instance.descendants():
        col.project = to_project_instance
        col.save()
        print(f"Collection({col.id})")
        for res in col.resources.iterator():
            res.ptr_project = to_project_instance
            res.save()
            print(
                "Metadatas deleted: ",
                MetadataResourceValue.objects.filter(resource=res).delete(),
            )
            print(f"Resource({res.id})")
            if res.file:
                res.file.project = to_project_instance
                res.file.save()
                print(f"File({res.file.id})")
                ocr_task(res.file.id)
    print("Done.")


def give_access(user: Union[str, int], project: Union[str, int], role: Union[str, int]):
    """
    Give access to user. Params can either be ints for object pks or strings for usernames and labels.
    """
    user_instance = None
    if isinstance(user, int):
        user_instance = User.objects.filter(pk=user).fist()
    if not user_instance:
        user_instance = User.objects.filter(username=user).first()
    if not user_instance:
        print(f'Utilisateur "{user}" introuvable')
    project_instance = None
    if isinstance(project, int):
        project_instance = Project.objects.filter(pk=project).fist()
    if not project_instance:
        project_instance = Project.objects.filter(label=project).first()
    if not project_instance:
        print(f'Projet "{project}" introuvable')
    role_instance = None
    if isinstance(role, int):
        role_instance = Role.objects.filter(project=project_instance, pk=role).first()
    if not role_instance:
        role_instance = Role.objects.filter(
            project=project_instance, label=role
        ).first()
    if not role_instance:
        print(f'Rôle "{role}" introuvable')
    if not role_instance or not user_instance or not project_instance:
        return
    return ProjectAccess.objects.get_or_create(
        role=role_instance, project=project_instance, user=user_instance
    )


def get_or_create_project(project_label: str) -> Project:
    """
    Get or creates a project based on given label.
    """
    project_label = project_label.strip()
    if not project_label:
        raise ValueError("needs a non-empty label")

    def add_dc_metas(project: Project, add_atlas_extras: bool = False):
        DC_METAS = [
            ["title", "A name given to the resource"],
            ["creator", "An entity primarily responsible for making the resource."],
            ["subject", "The topic of the resource."],
            ["description", "An account of the resource."],
            ["publisher", "An entity responsible for making the resource available."],
            [
                "contributor",
                "An entity responsible for making contributions to the resource.",
            ],
            [
                "date",
                "A point or period of time associated with an event in the lifecycle of the resource.",
            ],
            ["type", "The nature or genre of the resource."],
            [
                "format",
                "The file format, physical medium, or dimensions of the resource.",
            ],
            [
                "identifier",
                "An unambiguous reference to the resource within a given context.",
            ],
            [
                "source",
                "A related resource from which the described resource is derived.",
            ],
            ["language", "A language of the resource."],
            ["relation", "A related resource."],
            [
                "coverage",
                "The spatial or temporal topic of the resource, the spatial applicability of the resource, or the jurisdiction under which the resource is relevant.",
            ],
            ["rights", "Information about rights held in and over the resource."],
            [
                "audience",
                "A class of entity for whom the resource is intended or useful.",
            ],
            [
                "provenance",
                "A statement of any changes in ownership and custody of the resource since its creation that are significant for its authenticity, integrity, and interpretation.",
            ],
            [
                "rightsholder",
                "A person or organization owning or managing rights over the resource.",
            ],
        ]
        dc_set, _ = MetadataSet.objects.get_or_create(
            title="Dublin_Core", project=project
        )
        rank = 1
        for m in DC_METAS:
            meta, _ = Metadata.objects.get_or_create(
                title=m[0], set_id=dc_set.pk, project=project, rank=rank
            )
            rank = rank + 1
        return dc_set

    project = Project.objects.filter(label__iexact=project_label).first()
    if not project:
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
        add_dc_metas(project)
        project.root_collection
    return project


def version():
    from jama import __version__ as v

    return v


def bpython(self, options):
    import bpython

    bpython.embed(
        {
            "APIKey": APIKey,
            "Collection": Collection,
            "File": File,
            "Permission": Permission,
            "Project": Project,
            "ProjectAccess": ProjectAccess,
            "Resource": Resource,
            "User": User,
            "ProjectProperty": ProjectProperty,
            "UserTask": UserTask,
            "Tag": Tag,
            "FileExtension": FileExtension,
            "FileType": FileType,
            "MetadataSet": MetadataSet,
            "Metadata": Metadata,
            "MetadataCollectionValue": MetadataCollectionValue,
            "MetadataResourceValue": MetadataResourceValue,
            "CollectionMembership": CollectionMembership,
            "Role": Role,
            "projects": projects,
            "users": users,
            "accesses": accesses,
            "make_iiif": make_iiif,
            "make_ocr": make_ocr,
            "give_access": give_access,
            "version": version,
            "get_or_create_project": get_or_create_project,
            # "move_collection_to_project": move_collection_to_project,
        }
    )


Command.bpython = bpython
