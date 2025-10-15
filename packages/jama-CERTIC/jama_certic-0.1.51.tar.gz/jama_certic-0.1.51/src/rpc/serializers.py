from resources import models
from jama import settings
import os
from rpc.cache import SerializerCache


def get_cache(cache: SerializerCache = None):
    if not cache:
        return SerializerCache()
    return cache


def iiif_file_exists(file_hash) -> bool:
    path_to_test = "{}/{}".format(
        settings.IIIF_DIR, models.hash_to_iiif_path(file_hash)
    )
    return os.path.isfile(path_to_test)


def file_type(ftype: models.FileType, cache: SerializerCache = None) -> dict:
    extensions = []
    for ext in ftype.extensions.all():
        extensions.append(ext.label)
    return {
        "mime": ftype.mime,
        "extensions": extensions,
        "iiif_support": ftype.serve_with_iiif,
    }


def metadataset(
    metadataset_instance: models.MetadataSet, cache: SerializerCache = None
) -> dict:
    return {
        "object_type": "metadataset",
        "id": metadataset_instance.id,
        "title": metadataset_instance.title,
        "project_id": metadataset_instance.project_id,
        "metas_count": metadataset_instance.metadata_set.filter(expose=True).count(),
    }


def metadata(metadata_instance: models.Metadata, cache: SerializerCache = None) -> dict:
    set_instance = get_cache(cache).fetch_obj("metadataset", metadata_instance.set_id)
    return {
        "object_type": "metadata",
        "id": metadata_instance.id,
        "title": metadata_instance.title,
        "set_id": metadata_instance.set_id,
        "set_title": set_instance.title,
        "rank": metadata_instance.rank,
        "project_id": metadata_instance.project_id,
    }


def metadata_collection_value(
    metadata_collection_value_instance: models.MetadataCollectionValue,
    cache: SerializerCache = None,
) -> dict:
    metadata_instance = get_cache(cache).fetch_obj(
        "metadata", metadata_collection_value_instance.metadata_id
    )
    return {
        "object_type": "metadata_collection_value",
        "id": metadata_collection_value_instance.id,
        "meta": metadata(metadata_instance, cache=cache),
        "value": metadata_collection_value_instance.value,
    }


def metadata_resource_value(
    metadata_resource_value_instance: models.MetadataResourceValue,
    cache: SerializerCache = None,
) -> dict:
    metadata_instance = get_cache(cache).fetch_obj(
        "metadata", metadata_resource_value_instance.metadata_id
    )
    return {
        "object_type": "metadata_resource_value",
        "id": metadata_resource_value_instance.id,
        "meta": metadata(metadata_instance, cache=cache),
        "value": metadata_resource_value_instance.value,
    }


def collection(
    collection_instance: models.Collection,
    recursive: bool = False,
    only_published: bool = False,
    cache: SerializerCache = None,
) -> dict:
    tags = []
    for tag_instance in collection_instance.tags.all():
        tags.append(tag(tag_instance, cache=cache))
    payload = {
        "object_type": "collection",
        "id": collection_instance.id,
        "title": collection_instance.title,
        "resources_count": collection_instance.resources.filter(
            deleted_at__isnull=True
        ).count(),
        "children_count": collection_instance.children()
        .filter(deleted_at__isnull=True)
        .count(),
        "parent": collection_instance.parent_id,
        "children": None,
        "project_id": collection_instance.project_id,
        "metas": [],
        "public_access": collection_instance.public_access,
        "published_at": collection_instance.published_at.isoformat()
        if collection_instance.published_at
        else None,
        "tags": tags,
        "represented_by": (
            resource(collection_instance.representative, False, cache=cache)
            if collection_instance.representative
            and collection_instance.representative.deleted_at is None
            else None
        ),
        "created_at": collection_instance.created_at.isoformat(),
        "updated_at": collection_instance.updated_at.isoformat(),
        "ark": collection_instance.ark,
        "ancestors": [
            {"id": x.pk, "title": x.title} for x in collection_instance.ancestors()
        ][1:],
    }
    if recursive:
        payload["children"] = []
        for child in collection_instance.children():
            # filter private content
            if only_published and child.public_access is False:
                continue
            payload["children"].append(collection(child, recursive, cache=cache))

    for prop in collection_instance.metadatacollectionvalue_set.all():
        payload["metas"].append(metadata_collection_value(prop, cache=cache))

    return payload


def resource(
    resource_instance: models.Resource,
    include_metas: bool = True,
    cache: SerializerCache = None,
) -> dict:
    try:
        if resource_instance.file:
            return file(resource_instance.file, include_metas, cache=cache)
    except models.File.DoesNotExist:
        pass
    tags = []
    for tag_instance in resource_instance.tags.all():
        tags.append(tag(tag_instance, cache=cache))
    return {
        "object_type": "resource",
        "id": resource_instance.id,
        "title": resource_instance.title,
        "tags": tags,
        "created_at": resource_instance.created_at.isoformat(),
        "updated_at": resource_instance.updated_at.isoformat(),
        "ark": resource_instance.ark,
        "project_id": resource_instance.ptr_project_id,
    }


def file(
    file_instance: models.File,
    include_metas: bool = True,
    cache: SerializerCache = None,
) -> dict:
    props = []
    urls = {
        "download": "{}rpc/download/{}".format(settings.JAMA_SITE, file_instance.pk),
        "download_public": "{}rpc/download_public/{}".format(
            settings.JAMA_SITE, file_instance.hash
        ),
        "serve": "{}rpc/serve/{}".format(settings.JAMA_SITE, file_instance.hash),
    }
    tags = []
    for tag_instance in file_instance.tags.all():
        tags.append(tag(tag_instance, cache=cache))
    if (
        file_instance.should_have_iiif
    ):  # and iiif_file_exists(file_instance.hash): # FS is slow
        iiif_path = models.hash_to_iiif_path(
            file_instance.hash, settings.IIIF_PATH_SEPARATOR
        )
        urls["iiif"] = "{}{}/info.json".format(settings.JAMA_IIIF_ENDPOINT, iiif_path)
        urls["s"] = "{}{}/full/{}100,/0/default.jpg".format(
            settings.JAMA_IIIF_ENDPOINT, iiif_path, settings.JAMA_IIIF_UPSCALING_PREFIX
        )
        urls["m"] = "{}{}/full/{}300,/0/default.jpg".format(
            settings.JAMA_IIIF_ENDPOINT, iiif_path, settings.JAMA_IIIF_UPSCALING_PREFIX
        )
        urls["l"] = "{}{}/full/{}1000,/0/default.jpg".format(
            settings.JAMA_IIIF_ENDPOINT, iiif_path, settings.JAMA_IIIF_UPSCALING_PREFIX
        )
        urls["xl"] = "{}{}/full/{}5000,/0/default.jpg".format(
            settings.JAMA_IIIF_ENDPOINT, iiif_path, settings.JAMA_IIIF_UPSCALING_PREFIX
        )
    if include_metas:
        # This will NOT use the prefetched data and will generate a HUGE
        # number of queries with large sets of resources (see Herbier Corbières):
        #
        # for prop in file_instance.metadataresourcevalue_set.filter(
        #    metadata__expose=True
        # ).order_by("-metadata__set", "metadata__rank", "id"):
        #    props.append(metadata_resource_value(prop, cache=cache))
        #
        # Slightly different result but much less
        for prop in file_instance.metadataresourcevalue_set.all():
            if prop.metadata.expose:
                props.append(metadata_resource_value(prop, cache=cache))
        props = sorted(props, key=lambda d: d["meta"]["id"])

    file_type_instance = get_cache(cache).fetch_obj(
        "file_type", file_instance.file_type_id
    )
    return {
        "object_type": "resource",
        "id": file_instance.id,
        "title": file_instance.title,
        "original_name": file_instance.original_name,
        "type": str(file_type_instance),
        "hash": file_instance.hash,
        "metas": props or None,
        "urls": urls,
        "tags": tags,
        "created_at": file_instance.created_at.isoformat(),
        "updated_at": file_instance.updated_at.isoformat(),
        "project_id": file_instance.project.id,
        "ark": file_instance.ark,
        "width": file_instance.image_width(),
        "height": file_instance.image_height(),
    }


def tag(tag_instance: models.Tag, cache: SerializerCache = None) -> dict:
    return {
        "object_type": "tag",
        "id": tag_instance.id,
        "uid": tag_instance.uid,
        "label": tag_instance.label or tag_instance.uid,
        "ark": tag_instance.ark,
    }


def project(project_instance: models.Project, cache: SerializerCache = None) -> dict:
    return {
        "object_type": "project",
        "id": project_instance.pk,
        "label": project_instance.label,
        "description": project_instance.description,
    }


def permission(
    permission_instance: models.Permission, cache: SerializerCache = None
) -> dict:
    return {
        "object_type": "permission",
        "id": permission_instance.pk,
        "label": permission_instance.label,
    }


def role(role_instance: models.Role, cache: SerializerCache = None) -> dict:
    permissions = []
    for permission_instance in role_instance.permissions.all():
        permissions.append(permission(permission_instance, cache=cache))
    return {
        "object_type": "role",
        "id": role_instance.id,
        "label": role_instance.label,
        "permissions": permissions,
    }


def project_access(
    project_access_instance: models.ProjectAccess, cache: SerializerCache = None
) -> dict:
    cache = get_cache(cache)
    role_instance = cache.fetch_obj("role", project_access_instance.role_id)
    project_instance = cache.fetch_obj("project", project_access_instance.project_id)
    user_instance = cache.fetch_obj("user", project_access_instance.user_id)
    return {
        "object_type": "project_access",
        "project": project(project_instance, cache=cache),
        "role": role(role_instance, cache=cache),
        "user": user_instance.username,
    }


def project_property(
    project_property_instance: models.ProjectProperty, cache: SerializerCache = None
) -> dict:
    return {
        "project_id": project_property_instance.project_id,
        "key": project_property_instance.key,
        "value": project_property_instance.value,
    }


def user_task(user_task_instance: models.UserTask) -> dict:
    return {
        "object_type": "task",
        "id": user_task_instance.id,
        "description": user_task_instance.description,
        "created_at": (
            user_task_instance.created_at.isoformat()
            if user_task_instance.created_at
            else None
        ),
        "started_at": (
            user_task_instance.started_at.isoformat()
            if user_task_instance.started_at
            else None
        ),
        "finished_at": (
            user_task_instance.finished_at.isoformat()
            if user_task_instance.finished_at
            else None
        ),
        "failed_at": (
            user_task_instance.failed_at.isoformat()
            if user_task_instance.failed_at
            else None
        ),
        "project_id": user_task_instance.project_id,
    }
