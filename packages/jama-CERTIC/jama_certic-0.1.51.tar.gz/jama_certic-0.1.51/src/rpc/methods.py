import logging
import os
import re
from datetime import timedelta
from functools import wraps as _wraps
from glob import glob as _glob
from inspect import signature as _signature
from typing import List, Dict, Iterator, Union, Tuple
import cv2
import numpy
import pyvips
import unidecode
from deskew import determine_skew as _determine_skew
from django.contrib.auth.models import User
from django.db.models import QuerySet
from django.db.utils import IntegrityError
from django.utils import timezone

from jama import settings
from resources import tasks
from resources.helpers import (
    handle_local_file as _handle_local_file,
    set_exif_metas as _set_exif_metas,
)
from resources.models import (
    Resource,
    MetadataSet,
    Metadata,
    Collection,
    File,
    FileType,
    MetadataResourceValue,
    MetadataCollectionValue,
    Tag,
    Project,
    ProjectAccess,
    Role,
    Permission,
    APIKey,
    ProjectProperty,
    UserTask,
    XLSX_MULTIPLE_VALUES_SEPARATOR,
)

from annotations.models import Annotation

from rpc import serializers
from rpc.cache import SerializerCache
from rpc.const import (
    CANT_CREATE_IMAGE,
    COLLECTION_ALREADY_EXIST_IN_PARENT,
    INVALID_PROPERTY_KEY,
    NO_FOOTGUNS,
    NO_METADATASET_MIX,
    NO_PATH,
    NO_PROJECT_ACCESS,
    NO_PROJECT_ID,
    NO_SUCH_COLLECTION,
    NO_SUCH_METADATA,
    NO_SUCH_METADATASET,
    NO_SUCH_PROJECT_PROPERTY,
    NO_SUCH_PROJECT,
    NO_SUCH_RESOURCE,
    NO_SUCH_TAG,
    NO_SUCH_USER,
    NOT_A_FILE,
    NOT_AN_IMAGE,
    NOTHING_TO_DO,
    PERM_COLLECTION_CREATE,
    PERM_COLLECTION_DELETE,
    PERM_COLLECTION_READ,
    PERM_COLLECTION_UPDATE,
    PERM_METADATA_CREATE,
    PERM_METADATA_DELETE,
    PERM_METADATA_READ,
    PERM_METADATA_UPDATE,
    PERM_METADATASET_CREATE,
    PERM_METADATASET_DELETE,
    PERM_METADATASET_READ,
    PERM_PERMISSION_UPDATE,
    PERM_PROJECT_PROPERTY_CREATE,
    PERM_PROJECT_PROPERTY_DELETE,
    PERM_PROJECT_PROPERTY_READ,
    PERM_PROJECT_PROPERTY_UPDATE,
    PERM_RESOURCE_DELETE,
    PERM_RESOURCE_READ,
    PERM_RESOURCE_UPDATE,
    PERM_ROLE_READ,
    PERM_TAG_DELETE,
    PROJECT_MISMATCH,
    SEARCH_TERMS_LIMIT,
    SUPERUSER_NEEDED,
    TOO_MANY_SEARCH_TERMS,
    UNKNOWN_ERROR,
    WRONG_ARGUMENT,
)
from django.db.models.functions import Cast
from django.db.models import BinaryField

logger = logging.getLogger(__name__)


class ServiceException(Exception):
    """
    Base exception for all RPC methods.
    Accepts a message
    """

    def __init__(self, *args, **kwargs):
        self.message = args[0]


def _deskew2(image_path: str) -> float:
    im = cv2.imread(image_path)
    height, width, _ = im.shape
    scale_factor = 1000 / max(height, width)
    height = int(height * scale_factor)
    width = int(width * scale_factor)
    im = cv2.resize(
        im,
        (width, height),
        interpolation=cv2.INTER_LINEAR,
    )
    im_gs = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
    angle = _determine_skew(im_gs)
    if angle:
        return angle * -1
    return 0.0


def _deskew(
    image_path: str, max_skew: int = 10, fast: bool = True, scale_max: int = 1000
) -> float:
    im = cv2.imread(image_path)
    height, width, _ = im.shape
    if fast:
        scale_factor = scale_max / max(height, width)
        height = int(height * scale_factor)
        width = int(width * scale_factor)
        im = cv2.resize(
            im,
            (width, height),
            interpolation=cv2.INTER_LINEAR,
        )
    im_gs = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
    im_gs = cv2.fastNlMeansDenoising(im_gs, h=3)
    im_bw = cv2.threshold(im_gs, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]
    lines = cv2.HoughLinesP(
        im_bw, 1, numpy.pi / 180, 30, minLineLength=width / 12, maxLineGap=width / 150
    )
    if lines is None:
        return 0.0
    if type(lines) is not numpy.ndarray:
        return 0.0
    if not lines.any():
        return 0.0
    # Collect the angles of these lines (in radians)
    angles = []
    for line in lines:
        x1, y1, x2, y2 = line[0]
        angles.append(numpy.arctan2(y2 - y1, x2 - x1))
    max_skew_in_deg = numpy.deg2rad(max_skew)
    angles = [angle for angle in angles if abs(angle) < max_skew_in_deg]
    if len(angles) < 5:
        # Insufficient data to deskew
        return 0

    # Average the angles to a degree offset
    angle_deg = numpy.rad2deg(numpy.median(angles))

    return angle_deg * -1


def _validate_limits(limit_from: int, limit_to: int) -> Tuple[int, int]:
    try:
        limit_from = int(limit_from)
        limit_to = int(limit_to)
        if limit_to < limit_from:
            raise ServiceException(WRONG_ARGUMENT)
    except ValueError:
        raise ServiceException(WRONG_ARGUMENT)
    return limit_from, limit_to


def _log_call(func):
    """
    (Decorator)

    Log API call

    DEPRECATED
    """

    @_wraps(func)
    def wrapper(*args, **kwargs):
        sign = _signature(func)
        param_names = []
        for param in list(sign.parameters.items())[1:]:
            param_names.append(param[0])
        params_dict = dict(zip(param_names, args[1:]))
        logger.info(
            'User {}({}) called "{}" with params {}.'.format(
                args[0].username, args[0].pk, func.__name__, params_dict
            )
        )
        return func(*args, **kwargs)

    return wrapper


def _require_superuser(func):
    """
    (Decorator)

    Force superuser check before function execution
    """

    @_wraps(func)
    def wrapper(*args, **kwargs):
        user = args[0]  # user MUST be first argument
        if not user or not user.is_superuser:
            raise ServiceException(SUPERUSER_NEEDED)
        return func(*args, **kwargs)

    return wrapper


def _rpc_groups(groups: List[str]):
    """
    (Decorator)

    Categorize the function by adding a rpc_groups
    property to it.
    """

    def decorator(func):
        @_wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        wrapper.rpc_groups = groups
        return wrapper

    return decorator


def _check_project_permission(
    user: User, project: Union[Project, int], permission: str
) -> Project:
    """
    Will raise a ServiceException if:
        - user has no access to given project/permission
        - project is int and no such pk exists
    """
    if project is None:
        raise ServiceException(NO_PROJECT_ID)
    if isinstance(project, int):
        try:
            project = Project.objects.get(pk=project)
        except Project.DoesNotExist:
            raise ServiceException(NO_SUCH_PROJECT)
    access = ProjectAccess.objects.filter(
        user=user, project=project, role__permissions__label=permission
    ).first()
    if access:
        return project
    raise ServiceException(
        NO_PROJECT_ACCESS.format(
            permission, project.label if isinstance(project, Project) else project
        )
    )


def _user_has_permission(
    user: User, project: Union[Project, int], permission: str
) -> bool:
    try:
        _check_project_permission(user, project, permission)
        return True
    except ServiceException:
        return False


# Define RPC functions here.
# ALL RPC functions receive a User instance as first argument


@_rpc_groups(["Utilities"])
def ping(user: User) -> str:
    """
    This is a test method to ensure the server-client communication works.
    Will return "pong [name authenticated of user]"

    Example output:

    ```
    pong john
    ```
    """
    return "pong {}".format(user.username)


@_rpc_groups(["Metadatas"])
def metadatasets(user: User, project_id: int) -> List[Dict]:
    """
    Get the list of all the project's metadata sets.
    For each metadatas set, the number of metadatas is given in metas_count.

    Example output:

    ```
    [
        {"id": 1, "title": "exif metas", "project_id": 1, "metas_count": 23},
        {"id": 2, "title": "dublin core", "project_id": 1, "metas_count": 17}
    ]
    ```
    """
    try:
        data = []
        # Get the project metadatasets AND the public metadatasets
        query_set: Iterator[MetadataSet] = MetadataSet.objects.filter(
            project=Project.objects.get(pk=project_id),
            project__projectaccess__user=user,
            project__projectaccess__role__permissions__label=PERM_METADATASET_READ,
        )
        serializer_cache = SerializerCache()
        for item in query_set:
            data.append(serializers.metadataset(item, cache=serializer_cache))
        return data
    except Project.DoesNotExist:
        raise ServiceException(NO_SUCH_PROJECT)


@_rpc_groups(["Metadatas"])
def metadatas(user: User, metadata_set_id: int) -> List[Dict]:
    """
    Get all metadatas given a metadata set id.

    Metadatas MAY be ordered with the rank attribute.

    Example output:

    ```
    [
        {
            "id": 1,
            "title": "PNG:ProfileName",
            "set_id": 1,
            "set_title": "exif metas",
            "rank": 0,
            "project_id": 1,
        },
        {
            "id": 2,
            "title": "ICC_Profile:GrayTRC",
            "set_id": 1,
            "set_title": "exif metas",
            "rank": 1,
            "project_id": 1,
        }
    ]
    ```
    """
    data = []
    query_set: Union[Iterator[MetadataSet], QuerySet] = MetadataSet.objects.filter(
        id=metadata_set_id,
        project__projectaccess__user=user,
        project__projectaccess__role__permissions__label=PERM_METADATASET_READ,
    )
    metadata_set: MetadataSet = query_set.first()
    if metadata_set:
        serializer_cache = SerializerCache()
        for metadata_instance in Metadata.objects.filter(set=metadata_set, expose=True):
            data.append(serializers.metadata(metadata_instance, cache=serializer_cache))
    return data


@_rpc_groups(["Metadatas"])
def metadata(user: User, metadata_id: int) -> Dict:
    """
    Get one particular metadata given its id.

    Example output:

    ```
    {
        "id": 2,
        "title": "ICC_Profile:GrayTRC",
        "set_id": 1,
        "set_title": "exif metas",
        "rank": 1,
        "project_id": 1,
    }
    ```
    """
    query_set: Union[Iterator[Collection], QuerySet] = Metadata.objects.filter(
        pk=metadata_id,
        project__projectaccess__user=user,
        project__projectaccess__role__permissions__label=PERM_METADATA_READ,
    )
    metadata_instance = query_set.first()
    if not metadata_instance:
        raise ServiceException(NO_SUCH_METADATA)
    return serializers.metadata(metadata_instance, cache=SerializerCache())


@_rpc_groups(["Collections"])
def collections(
    user: User,
    parent_id: int,
    recursive: bool = False,
    limit_from: int = 0,
    limit_to: int = 2000,
    flat_list: bool = False,
    only_published: bool = False,
    order_by: str = "title",
    only_deleted_items: bool = False,
) -> List[Dict]:
    """
    Return the user's collections under the parent collection
    specified by 'parent_id'. If 'recursive' is true, will
    return all the descendants recursively in the 'children' key.
    If recursive is false, 'children' is null.

    Special case:

    If flat_list is True, collections are returned as a flat list and parent_id is effectively IGNORED.

    Example output:

    ```
    [
        {
            "id": 2,
            "title": "art works",
            "resources_count": 23,
            "children_count": 5,
            "descendants_count": 12,
            "descendants_resources_count": 58,
            "parent": 1,
            "children": None,
            "metas": [],
            "public_access": False,
            "tags": [],
        }
    ]
    ```
    """
    available_order_by = [
        "title",
        "-title",
        "updated_at",
        "-updated_at",
        "created_at",
        "-created_at",
    ]
    try:
        assert order_by in available_order_by
    except AssertionError:
        raise ServiceException(
            WRONG_ARGUMENT
            + ": order_by must be one of {}".format(", ".join(available_order_by))
        )
    order_by = {
        "title": "title_binary",
        "-title": "-title_binary",
        "updated_at": "updated_at",
        "-updated_at": "-updated_at",
        "created_at": "created_at",
        "-created_at": "-created_at",
    }.get(order_by)
    try:
        parent = Collection.objects.get(
            pk=parent_id,
            deleted_at__isnull=not only_deleted_items,
            project__projectaccess__user=user,
            project__projectaccess__role__permissions__label=PERM_COLLECTION_READ,
        )
        project_id = parent.project_id
    except Collection.DoesNotExist:
        raise ServiceException(NO_SUCH_COLLECTION)
    limit_from, limit_to = _validate_limits(limit_from, limit_to)
    data = []
    if flat_list:
        query_set: Union[Iterator[Collection], QuerySet] = (
            Collection.objects.filter(
                project_id=project_id,
                deleted_at__isnull=not only_deleted_items,
                project__projectaccess__user=user,
                project__projectaccess__role__permissions__label=PERM_COLLECTION_READ,
            )
            .annotate(title_binary=Cast("title", output_field=BinaryField()))
            .order_by(order_by)
        )
    else:
        query_set: Union[Iterator[Collection], QuerySet] = (
            Collection.objects.filter(
                parent=parent,
                deleted_at__isnull=not only_deleted_items,
                project_id=project_id,
                project__projectaccess__user=user,
                project__projectaccess__role__permissions__label=PERM_COLLECTION_READ,
            )
            .annotate(title_binary=Cast("title", output_field=BinaryField()))
            .order_by(order_by)
        )
    if only_published:
        query_set = query_set.filter(public_access=True)
    query_set = query_set[limit_from:limit_to]
    serializer_cache = SerializerCache()
    for item in query_set:
        data.append(
            serializers.collection(
                item,
                recursive=recursive,
                only_published=only_published,
                cache=serializer_cache,
            )
        )
    return data


@_rpc_groups(["Collections"])
def collection(user: User, collection_id: int) -> Dict:
    """
    Get a particular collection given its id.

    Example output:

    ```
    {
        "id": 2,
        "title": "art works",
        "resources_count": 23,
        "children_count": 5,
        "parent": 1,
        "children": None,
        "metas": [],
        "public_access": False,
        "tags": [],
    }
    ```
    """
    collection_instance = Collection.objects.filter(
        pk=collection_id, deleted_at__isnull=True
    ).first()
    if not collection_instance:
        raise ServiceException(NO_SUCH_COLLECTION)
    _check_project_permission(user, collection_instance.project, PERM_COLLECTION_READ)

    return serializers.collection(collection_instance, cache=SerializerCache())


@_rpc_groups(["Collections"])
def add_collection(user: User, title: str, parent_id: int) -> Dict:
    """
    Create a new collection based on 'title' and parent_id

    Returns either the serialized new collection of null if parent does
    not exist.

    Example output:

    ```
    {
        "id": 3,
        "title": "paintings",
        "resources_count": 0,
        "children_count": 0,
        "descendants_count": 0,
        "descendants_resources_count": 0,
        "parent": null,
        "project_id": 1,
        "children": null,
        "metas": [],
        "public_access": false,
        "tags": [],
    }
    ```
    """
    # fetch parent, check parent's project add access
    parent = Collection.objects.filter(
        pk=parent_id,
        deleted_at__isnull=True,
        project__projectaccess__user=user,
        project__projectaccess__role__permissions__label=PERM_COLLECTION_READ,
    ).first()
    if not parent:
        raise ServiceException(NO_SUCH_COLLECTION)
    else:
        _check_project_permission(user, parent.project, PERM_COLLECTION_CREATE)

    collection_instance, created = Collection.objects.get_or_create(
        title=title, parent=parent, project_id=parent.project.pk
    )
    # collection was previously soft-deleted, reactivate it.
    if collection_instance.deleted_at:
        collection_instance.deleted_at = None
        collection_instance.save()
    return serializers.collection(collection_instance, cache=SerializerCache())


@_rpc_groups(["Collections"])
def add_collection_from_path(user: User, path: str, project_id: int) -> List[Dict]:
    """
    Will take a path such as '/photos/arts/paintings/'
    and build the corresponding hierarchy of collections. The hierarchy
    is returned as a list of serialized collections.

    Beware: Because the collections are serialized before their children,
    all the children/descendants counts are set to 0.

    Example output:

    ```
    [
        {
            "id": 1,
            "title": "photos",
            "resources_count": 0,
            "children_count": 0,
            "descendants_count": 0,
            "descendants_resources_count": 0,
            "parent": null,
            "project_id": 1,
            "children": null,
            "metas": [],
            "public_access": false,
            "tags": [],
        },
        {
            "id": 2,
            "title": "arts",
            "resources_count": 0,
            "children_count": 0,
            "descendants_count": 0,
            "descendants_resources_count": 0,
            "parent": 1,
            "project_id": 1,
            "children": null,
            "metas": [],
            "public_access": false,
            "tags": [],
        },
        {
            "id": 3,
            "title": "paintings",
            "resources_count": 0,
            "children_count": 0,
            "descendants_count": 0,
            "descendants_resources_count": 0,
            "parent": 2,
            "project_id": 1,
            "children": null,
            "metas": [],
            "public_access": false,
            "tags": [],
        },
    ]
    ```
    """
    if not path:
        raise ServiceException(NO_PATH)
    if not project_id:
        raise ServiceException(NO_PROJECT_ID)
    project = Project.objects.filter(pk=project_id).first()
    if not project:
        raise ServiceException(NO_SUCH_PROJECT)
    _check_project_permission(user, project, PERM_COLLECTION_CREATE)
    hierarchy = []
    previous_dir = project.root_collection
    serializer_cache = SerializerCache()
    for dir_name in path.split("/"):
        # force ascii representation of unicode strings
        dir_name = unidecode.unidecode(dir_name.strip())
        if dir_name:
            previous_dir, created = Collection.objects.get_or_create(
                title=dir_name, parent=previous_dir, project=project
            )
            # if has been soft-deleted, undelete.
            if previous_dir.deleted_at:
                previous_dir.deleted_at = None
                previous_dir.save()
            hierarchy.append(
                serializers.collection(previous_dir, cache=serializer_cache)
            )
    return hierarchy


@_rpc_groups(["Metadatas"])
def delete_metadata(user: User, metadata_id: int) -> bool:
    """
    Delete metadata based on its id.
    """
    try:
        metadata_instance = Metadata.objects.get(
            pk=metadata_id,
            project__projectaccess__user=user,
            project__projectaccess__role__permissions__label=PERM_METADATA_DELETE,
        )
        metadata_instance.delete()
        return True
    except Metadata.DoesNotExist:
        raise ServiceException(NO_SUCH_METADATA)


@_rpc_groups(["Metadatas"])
def delete_metadataset(
    user: User, metadataset_id: int, recursive: bool = False
) -> Dict:
    """
    Delete metadata set based on its id. Optional recursive
    call.
    """
    query_set: Union[Iterator[MetadataSet], QuerySet] = MetadataSet.objects.filter(
        pk=metadataset_id,
        project__projectaccess__user=user,
        project__projectaccess__role__permissions__label=PERM_METADATASET_DELETE,
    )
    metadataset_instance = query_set.first()
    if not metadataset_instance:
        return {"success": False, "status": "can't find metadata set"}

    if recursive:
        for metada_instance in Metadata.objects.filter(
            set=metadataset_instance,
            project__projectaccess__user=user,
            project__projectaccess__role__permissions__label=PERM_METADATA_DELETE,
        ):
            metada_instance.delete()

    if metadataset_instance.metadata_set.count() > 0:
        return {"success": False, "status": "set has metas"}

    number_of_rows, details = metadataset_instance.delete()
    if number_of_rows >= 1:
        return {"success": True, "status": "all good"}
    else:
        return {
            "success": False,
            "status": "could not delete set for unknown reasons",
        }


@_rpc_groups(["Collections"])
def delete_collection(user: User, collection_id: int, recursive: bool = False) -> Dict:
    """
    Delete collection given its id.

    Collection MUST be empty of any content (no children collections and no resources),
    unless the 'recursive'parameter is set to True, in which case ALL descendants will be
    deleted.
    """
    query_set: Union[Iterator[Collection], QuerySet] = Collection.objects.filter(
        pk=collection_id, deleted_at__isnull=True
    )
    collection_instance = query_set.first()
    if not collection_instance:
        return {"success": True, "status": "does not exist"}
    _check_project_permission(user, collection_instance.project, PERM_COLLECTION_DELETE)
    if recursive:
        if has_permission(user, collection_instance.project, PERM_RESOURCE_DELETE):
            for resource_instance in collection_instance.resources.all():
                # is it in another collection ?
                if (
                    resource_instance.collections.filter(
                        deleted_at__isnull=True
                    ).count()
                    < 2
                ):
                    resource_instance.soft_delete()
            for resource_instance in collection_instance.descendants_resources():
                # is it in another collection ?
                if (
                    resource_instance.collections.filter(
                        deleted_at__isnull=True
                    ).count()
                    < 2
                ):
                    resource_instance.soft_delete()
        for descendant_collection_instance in collection_instance.descendants():
            descendant_collection_instance.soft_delete()

    # do not allow to delete collection with content
    if len(collection_instance.children()) > 0:
        return {"success": False, "status": "collection has descendants"}
    collection_instance.soft_delete()
    return {"success": True, "status": "all good"}


@_rpc_groups(["Collections"])
def rename_collection(user: User, collection_id: int, title: str) -> bool:
    """
    Rename a collection (ie. change its title).
    """
    query_set: Union[Iterator[Collection], QuerySet] = Collection.objects.filter(
        pk=collection_id, deleted_at__isnull=True
    )
    collection_instance = query_set.first()
    if not collection_instance:
        raise ServiceException(NO_SUCH_COLLECTION)
    _check_project_permission(user, collection_instance.project, PERM_COLLECTION_UPDATE)
    collection_instance.title = title
    try:
        collection_instance.save()
    except IntegrityError:
        return False
    return True


@_rpc_groups(["Resources"])
def rename_resource(user: User, resource_id: int, title: str) -> bool:
    """
    Rename a resource (ie. change its title).
    """
    query_set: Union[Iterator[Resource], QuerySet] = Resource.objects.filter(
        pk=resource_id, deleted_at__isnull=True
    )
    resource_instance = query_set.first()
    if not resource_instance:
        raise ServiceException(NO_SUCH_RESOURCE)
    _check_project_permission(user, resource_instance.ptr_project, PERM_RESOURCE_UPDATE)
    resource_instance.title = title
    resource_instance.save()
    return True


@_rpc_groups(["Metadatas"])
def rename_meta(user: User, meta_id: int, title: str) -> bool:
    """
    Rename a metadata (ie. change its title).
    """
    query_set: Union[Iterator[Metadata], QuerySet] = Metadata.objects.filter(pk=meta_id)
    meta_instance = query_set.first()
    if not meta_instance:
        raise ServiceException(NO_SUCH_METADATA)
    _check_project_permission(user, meta_instance.project, PERM_METADATA_UPDATE)
    meta_instance.title = title
    meta_instance.save()
    return True


@_rpc_groups(["Resources"])
def resources(
    user: User,
    collection_id: int,
    include_metas: bool = False,
    limit_from: int = 0,
    limit_to: int = 2000,
    order_by: str = "title",
    only_deleted_items: bool = False,
    only_tags: List[str] = None,
) -> List[Dict]:
    """
    Get all resources from a collection.

    If 'include_metas' is true, will return the resources metadatas.
    If 'include_metas' is false, 'metas' will be null.

    Different resources types may have different object keys. The bare
    minimum is 'id', 'title' and 'tags'.

    Example output (file resource):

    ```
    [
        {
            "id": 1,
            "title": "letter",
            "original_name": "letter.txt",
            "type": "text/plain",
            "hash": "0dd93a59aeaccfb6d35b1ff5a49bde1196aa90dfef02892f9aa2ef4087d8738e",
            "metas": null,
            "urls": [],
            "tags": [],
        }
    ]
    ```
    """
    available_order_by = [
        "title",
        "-title",
        "updated_at",
        "-updated_at",
        "created_at",
        "-created_at",
        "collections__collectionmembership__rank",
        "-collections__collectionmembership__rank",
    ]
    try:
        assert order_by in available_order_by
    except AssertionError:
        raise ServiceException(
            WRONG_ARGUMENT
            + ": order_by must be one of {}".format(", ".join(available_order_by))
        )
    order_by = {
        "title": "title_binary",
        "-title": "-title_binary",
        "updated_at": "updated_at",
        "-updated_at": "-updated_at",
        "created_at": "created_at",
        "-created_at": "-created_at",
        "collections__collectionmembership__rank": "collections__collectionmembership__rank",
        "-collections__collectionmembership__rank": "-collections__collectionmembership__rank",
    }.get(order_by)
    try:
        Collection.objects.get(pk=collection_id)
    except Collection.DoesNotExist:
        raise ServiceException(NO_SUCH_COLLECTION)
    data = []
    limit_from, limit_to = _validate_limits(limit_from, limit_to)
    query_set: Union[Iterator[Resource], QuerySet] = (
        Resource.objects.filter(
            collections__id=collection_id,
            deleted_at__isnull=not only_deleted_items,
            ptr_project__projectaccess__user=user,
            ptr_project__projectaccess__role__permissions__label=PERM_RESOURCE_READ,
        )
        .select_related("file", "file__project")
        .prefetch_related("file__tags")
    )

    if include_metas:
        query_set = query_set.prefetch_related(
            "file__metadataresourcevalue_set",
            "file__metadataresourcevalue_set__metadata",
            "file__metadataresourcevalue_set__metadata__set",
        )

    if only_tags:
        query_set = query_set.filter(tags__uid__in=only_tags)

    query_set = query_set.annotate(
        title_binary=Cast("title", output_field=BinaryField())
    ).order_by(order_by)
    query_set = query_set.distinct()
    serializer_cache = SerializerCache()
    for item in query_set[limit_from:limit_to].iterator(chunk_size=2000):
        data.append(
            serializers.resource(
                item, include_metas=bool(include_metas), cache=serializer_cache
            )
        )
    return data


@_rpc_groups(["Resources"])
def resource(user: User, resource_id: int, include_metas: bool = True) -> Dict:
    """
    Get a resource given its id.

    Example output (file resource):

    ```
    {
        "id": 1,
        "title": "letter",
        "original_name": "letter.txt",
        "type": "text/plain",
        "hash": "0dd93a59aeaccfb6d35b1ff5a49bde1196aa90dfef02892f9aa2ef4087d8738e",
        "metas": null,
        "urls": [],
        "tags": [],
    }
    ```
    """
    query_set: Union[Iterator[Resource], QuerySet] = Resource.objects.filter(
        pk=resource_id, deleted_at__isnull=True
    )
    resource_instance = query_set.first()
    if not resource_instance:
        raise ServiceException(NO_SUCH_RESOURCE)
    _check_project_permission(user, resource_instance.ptr_project, PERM_RESOURCE_READ)
    return serializers.resource(
        resource_instance, include_metas=include_metas, cache=SerializerCache()
    )


@_rpc_groups(["Resources", "Collections"])
def add_resource_to_collection(
    user: User, resource_id: int, collection_id: int
) -> bool:
    """
    Add a resource to a collection given ids.
    """
    try:
        collection_instance = Collection.objects.get(
            pk=collection_id, deleted_at__isnull=True
        )
        resource_instance = Resource.objects.get(
            pk=resource_id,
            deleted_at__isnull=True,
            ptr_project=collection_instance.project,
        )
        _check_project_permission(
            user,
            collection_instance.project,
            PERM_COLLECTION_UPDATE,
        )
        _check_project_permission(
            user,
            resource_instance.ptr_project,
            PERM_RESOURCE_READ,
        )
        collection_instance.resources.add(resource_instance)
        return True
    except Collection.DoesNotExist:
        raise ServiceException(NO_SUCH_COLLECTION)
    except Resource.DoesNotExist:
        raise ServiceException(NO_SUCH_RESOURCE)


@_rpc_groups(["Resources", "Collections"])
def remove_resource_from_collection(
    user: User, resource_id: int, collection_id: int
) -> bool:
    """
    Remove a resource from a collection given ids.
    """
    try:
        collection_instance = Collection.objects.get(
            id=collection_id, deleted_at__isnull=True
        )
        resource_instance = Resource.objects.get(
            id=resource_id,
            deleted_at__isnull=True,
            ptr_project=collection_instance.project,
        )
        _check_project_permission(
            user,
            collection_instance.project,
            PERM_COLLECTION_UPDATE,
        )
        _check_project_permission(
            user,
            resource_instance.ptr_project,
            PERM_RESOURCE_READ,
        )
        collection_instance.resources.remove(resource_instance)
        return True
    except Collection.DoesNotExist:
        raise ServiceException(NO_SUCH_COLLECTION)
    except Resource.DoesNotExist:
        raise ServiceException(NO_SUCH_RESOURCE)


@_rpc_groups(["Resources"])
def delete_resource(user: User, resource_id: int) -> bool:
    """
    Permanently (soft) delete a resource given its id.
    """
    query_set: Union[Iterator[Resource], QuerySet] = Resource.objects.filter(
        pk=resource_id, deleted_at__isnull=True
    )
    resource_instance = query_set.first()
    if not resource_instance:
        return True
    _check_project_permission(user, resource_instance.ptr_project, PERM_RESOURCE_DELETE)
    # break link with current collections
    for current_collection in resource_instance.collections.all():
        remove_resource_from_collection(
            user, resource_instance.pk, current_collection.pk
        )
    resource_instance.soft_delete()
    return True


@_rpc_groups(["Search"])
def simple_search(
    user: User,
    query: str,
    project_id: int,
    limit_from: int = 0,
    limit_to: int = 2000,
    order_by: str = "title",
) -> Dict[str, List]:
    """
    Performs a simple search on resources and collections, based on their titles.

    Example output:

    ```
    {
        "collections": [
            {
            "id": 1,
            "title": "photos",
            "resources_count": 0,
            "children_count": 0,
            "descendants_count": 0,
            "descendants_resources_count": 0,
            "parent": null,
            "children": null,
            "metas": [],
            "public_access": false,
            "tags": [],
            }
        ],
        "resources": [
            {
            "id": 1,
            "title": "letter",
            "original_name": "letter.txt",
            "type": "text/plain",
            "hash": "0dd93a59aeaccfb6d35b1ff5a49bde1196aa90dfef02892f9aa2ef4087d8738e",
            "metas": null,
            "urls": [],
            "tags": [],
            }
        ]
    }
    ```
    """
    available_order_by = [
        "title",
        "-title",
        "updated_at",
        "-updated_at",
        "created_at",
        "-created_at",
    ]
    try:
        assert order_by in available_order_by
    except AssertionError:
        raise ServiceException(
            WRONG_ARGUMENT
            + ": order_by must be one of {}".format(", ".join(available_order_by))
        )

    limit_from, limit_to = _validate_limits(limit_from, limit_to)
    project = Project.objects.filter(pk=project_id).first()
    _check_project_permission(user, project, PERM_COLLECTION_READ)
    _check_project_permission(user, project, PERM_RESOURCE_READ)
    results = {"collections": [], "resources": []}
    collections_set: Union[Iterator[Collection], QuerySet] = Collection.objects.filter(
        title__icontains=query, deleted_at__isnull=True, project=project
    )
    serializer_cache = SerializerCache()
    for collection_instance in collections_set.distinct().order_by(order_by)[
        limit_from:limit_to
    ]:
        results["collections"].append(
            serializers.collection(collection_instance, cache=serializer_cache)
        )
    resources_set: Union[Iterator[Resource], QuerySet] = Resource.objects.filter(
        title__icontains=query, deleted_at__isnull=True, ptr_project=project
    )
    for resource_instance in resources_set.distinct().order_by(order_by)[
        limit_from:limit_to
    ]:
        results["resources"].append(
            serializers.resource(
                resource_instance, include_metas=False, cache=serializer_cache
            )
        )

    return results


@_rpc_groups(["Search"])
def advanced_search_terms(user: User) -> List[str]:
    """
    Return terms conditions to be used in advanced search.

    Example output:

    ```
    [
        "is",
        "contains",
        "does_not_contain"
    ]
    ```
    """
    return ["is", "contains", "does_not_contain"]


@_rpc_groups(["Search"])
def advanced_search(
    user: User,
    search_terms: List[Dict],
    project_id: int,
    include_metas: bool = False,
    collection_id: int = None,
    limit_from: int = 0,
    limit_to: int = 2000,
    order_by: str = "title",
    fetch_resources: bool = True,
    fetch_collections: bool = True,
    public_access: bool = None,
) -> Dict[str, List]:
    """
    Performs a complex search using terms such as 'contains', 'is', 'does_not_contain'.

    Multiple conditions can be added.

    Example input:

    ```
    [
        {"property": "title", "term": "contains", "value": "cherbourg"},
        {"meta": 123, "term": "is", "value": "35mm"},
        {"exclude_meta": 145},
        {"tags": ["PAINTINGS", "PHOTOS"]}
        {"exclude_tags": ["DRAWINGS"]}
    ]
    ```

    Example output:

    ```
    {
        "collections": [],
        "resources": [
            {
            "id": 1,
            "title": "Cherbourg by night",
            "original_name": "cherbourg_by_night.jpg",
            "type": "image/jpeg",
            "hash": "0dd93a59aeaccfb6d35b1ff5a49bde1196aa90dfef02892f9aa2ef4087d8738e",
            "metas": null,
            "urls": [],
            "tags": [],
            }
        ]
    }
    ```
    """
    available_order_by = [
        "title",
        "-title",
        "updated_at",
        "-updated_at",
        "created_at",
        "-created_at",
    ]
    try:
        assert order_by in available_order_by
    except AssertionError:
        raise ServiceException(
            WRONG_ARGUMENT
            + ": order_by must be one of {}".format(", ".join(available_order_by))
        )
    order_by = {
        "title": "title_binary",
        "-title": "-title_binary",
        "updated_at": "updated_at",
        "-updated_at": "-updated_at",
        "created_at": "created_at",
        "-created_at": "-created_at",
    }.get(order_by)

    limit_from, limit_to = _validate_limits(limit_from, limit_to)
    if len(search_terms) > SEARCH_TERMS_LIMIT:
        raise ServiceException(TOO_MANY_SEARCH_TERMS)
    project = Project.objects.filter(pk=project_id).first()
    _check_project_permission(user, project, PERM_COLLECTION_READ)
    _check_project_permission(user, project, PERM_RESOURCE_READ)
    results = {
        "collections": [],
        "resources": [],
        "collections_count": 0,
        "resources_count": 0,
    }

    if fetch_resources:
        # Search Resources first
        resources_set = Resource.objects.filter(
            ptr_project=project, deleted_at__isnull=True
        )
        if collection_id:
            resources_set = resources_set.filter(
                collectionmembership__collection_id=collection_id
            )
        if public_access is not None:
            resources_set = resources_set.filter(
                collectionmembership__collection__public_access=public_access
            )

        for search_term in search_terms:
            if (
                "property" in search_term
                and "term" in search_term
                and "value" in search_term
            ):
                if search_term["property"] == "title":
                    if search_term["term"] == "is":
                        resources_set = resources_set.filter(
                            title__iexact=search_term["value"]
                        )
                    if search_term["term"] == "contains":
                        resources_set = resources_set.filter(
                            title__icontains=search_term["value"]
                        )
                    if search_term["term"] == "does_not_contain":
                        resources_set = resources_set.exclude(
                            title__icontains=search_term["value"]
                        )
            elif (
                "meta" in search_term
                and "term" in search_term
                and "value" in search_term
            ):
                if search_term["term"] == "is":
                    resources_set = resources_set.filter(
                        metadataresourcevalue__value__iexact=search_term["value"],
                        metadataresourcevalue__metadata_id=search_term["meta"],
                    )
                if search_term["term"] == "contains":
                    resources_set = resources_set.filter(
                        metadataresourcevalue__value__icontains=search_term["value"],
                        metadataresourcevalue__metadata_id=search_term["meta"],
                    )
                if search_term["term"] == "does_not_contain":
                    resources_set = resources_set.exclude(
                        metadataresourcevalue__value__icontains=search_term["value"],
                        metadataresourcevalue__metadata_id=search_term["meta"],
                    )
            elif "exclude_meta" in search_term:
                resources_set = resources_set.exclude(
                    metadataresourcevalue__metadata_id=search_term["exclude_meta"]
                )
            elif "tags" in search_term:
                resources_set = resources_set.filter(tags__uid__in=search_term["tags"])
            elif "exclude_tags" in search_term:
                resources_set = resources_set.exclude(
                    tags__uid__in=search_term["exclude_tags"]
                )
        serializer_cache = SerializerCache()
        results["resources_count"] = resources_set.distinct().count()
        for resource_instance in (
            resources_set.annotate(
                title_binary=Cast("title", output_field=BinaryField())
            )
            .distinct()
            .order_by(order_by)[limit_from:limit_to]
        ):
            results["resources"].append(
                serializers.resource(
                    resource_instance,
                    include_metas=include_metas,
                    cache=serializer_cache,
                )
            )
    if fetch_collections:
        # Search collections second
        collections_set = Collection.objects.filter(
            project=project, deleted_at__isnull=True
        )
        if public_access is not None:
            collections_set = collections_set.filter(public_access=public_access)
        if collection_id:
            collections_set = collections_set.filter(parent_id=collection_id)

        for search_term in search_terms:
            if (
                "property" in search_term
                and "term" in search_term
                and "value" in search_term
            ):
                if search_term["property"] == "title":
                    if search_term["term"] == "is":
                        collections_set = collections_set.filter(
                            title__iexact=search_term["value"]
                        )
                    if search_term["term"] == "contains":
                        collections_set = collections_set.filter(
                            title__icontains=search_term["value"]
                        )
                    if search_term["term"] == "does_not_contain":
                        collections_set = collections_set.exclude(
                            title__icontains=search_term["value"]
                        )
            elif (
                "meta" in search_term
                and "term" in search_term
                and "value" in search_term
            ):
                if search_term["term"] == "is":
                    collections_set = collections_set.filter(
                        metadatacollectionvalue__value__iexact=search_term["value"],
                        metadatacollectionvalue__metadata_id=search_term["meta"],
                    )
                if search_term["term"] == "contains":
                    collections_set = collections_set.filter(
                        metadatacollectionvalue__value__icontains=search_term["value"],
                        metadatacollectionvalue__metadata_id=search_term["meta"],
                    )
                if search_term["term"] == "does_not_contain":
                    collections_set = collections_set.exclude(
                        metadatacollectionvaluee__value__icontains=search_term["value"],
                        metadatacollectionvalue__metadata_id=search_term["meta"],
                    )
            elif "exclude_meta" in search_term:
                collections_set = collections_set.exclude(
                    metadatacollectionvalue__metadata_id=search_term["exclude_meta"]
                )
            elif "tags" in search_term:
                collections_set = collections_set.filter(
                    tags__uid__in=search_term["tags"]
                )
            elif "exclude_tags" in search_term:
                collections_set = collections_set.exclude(
                    tags__uid__in=search_term["exclude_tags"]
                )
        serializer_cache = SerializerCache()
        results["collections_count"] = collections_set.distinct().count()
        for collection_instance in (
            collections_set.annotate(
                title_binary=Cast("title", output_field=BinaryField())
            )
            .distinct()
            .order_by(order_by)[limit_from:limit_to]
        ):
            results["collections"].append(
                serializers.collection(collection_instance, cache=serializer_cache)
            )

    return results


@_rpc_groups(["Search", "Collections", "Resources"])
def project_items(
    user: User,
    search_terms: List[Dict],
    project_id: int,
    include_metas: bool = False,
    collection_id: int = None,
    limit_from: int = 0,
    limit_to: int = 2000,
    order_by: str = "title",
    public_access: bool = None,
) -> Dict[str, List]:
    """
    Alias to advanced_search.
    """
    return advanced_search(
        user,
        search_terms,
        project_id,
        include_metas,
        collection_id,
        limit_from,
        limit_to,
        order_by,
        public_access=public_access,
    )


@_rpc_groups(["Utilities"])
def upload_infos(user: User, sha256_hash: str, project_id: int) -> Dict:
    """
    Get information for an upload based on the file hash.

    Example output:

    ```
    {
        "status": "not available",
        "id": null,
        "available_chunks":[]
    }
    ```

    "status" being one of "not available", "available" or "incomplete"
    """
    infos = {"status": "not available", "id": None, "available_chunks": []}
    if re.match("[A-Fa-f0-9]{64}", sha256_hash) is not None:
        project = Project.objects.filter(pk=project_id).first()
        _check_project_permission(user, project, "file.read")
        try:
            file_instance = File.objects.get(
                hash=sha256_hash, project=project, deleted_at__isnull=True
            )
            infos["status"] = "available"
            infos["id"] = file_instance.id
        except File.DoesNotExist:
            partials_dir = "{}/{}-{}".format(
                settings.PARTIAL_UPLOADS_DIR, user.pk, sha256_hash
            )
            if os.path.isdir(partials_dir):
                infos["status"] = "incomplete"
                for path in _glob("{}/*.part".format(partials_dir)):
                    infos["available_chunks"].append(os.path.basename(path))
                    infos["available_chunks"].sort()
    return infos


@_rpc_groups(["Utilities"])
def supported_file_types(user: User) -> List[Dict]:
    """
    Get a list of all supported file type, complete with their mimes.

    Example output:

    ```
    [
        {
        "mime": "image/jpeg",
        "extensions": [".jpg", ".jpeg"],
        "iiif_support": true,
        }
    ]
    ```
    """
    ftypes = []
    serializer_cache = SerializerCache()
    for ftype in FileType.objects.all():
        ftypes.append(serializers.file_type(ftype, cache=serializer_cache))
    return ftypes


@_rpc_groups(["Metadatas"])
def add_metadataset(user: User, title: str, project_id: int) -> int:
    """
    Create new metadata set from title.
    """
    project = Project.objects.filter(pk=project_id).first()
    _check_project_permission(user, project, PERM_METADATASET_CREATE)
    metadataset_instance, created = MetadataSet.objects.get_or_create(
        project=project, title=title
    )
    return metadataset_instance.id


@_rpc_groups(["Metadatas"])
def add_metadata(user: User, title: str, metas_set_id: int) -> int:
    """
    Add a new metadata to metadata set.

    Set optional 'metadata_type_id'. Defaults to string type.
    """
    try:
        metas_set = MetadataSet.objects.get(pk=metas_set_id)
        _check_project_permission(user, metas_set.project, PERM_METADATA_CREATE)
        metadata_instance, created = Metadata.objects.get_or_create(
            project=metas_set.project, title=title, set=metas_set
        )
        return metadata_instance.id
    except (
        MetadataSet.DoesNotExist,
        MetadataSet.MultipleObjectsReturned,
    ):
        raise ServiceException(NO_SUCH_METADATASET)


@_rpc_groups(["Metadatas", "Resources"])
def remove_meta_value_from_resource(
    user: User, resource_id: int, meta_value_id: int
) -> bool:
    """
    Remove a meta_value from a resource given their ids.
    """
    query_set: Union[Iterator[Resource], QuerySet] = Resource.objects.filter(
        pk=resource_id, deleted_at__isnull=True
    )
    resource_instance = query_set.first()
    if not resource_instance:
        raise ServiceException(NO_SUCH_RESOURCE)
    # this is a resource.update permission, not a metadata.update
    _check_project_permission(user, resource_instance.ptr_project, PERM_RESOURCE_UPDATE)
    for meta_value in resource_instance.metadataresourcevalue_set.all():
        if meta_value.id == meta_value_id:
            meta_value.delete()
            return True
    return False


@_rpc_groups(["Metadatas", "Resources"])
def set_metas_to_resource(user: User, resource_id: int, metas: List[dict]) -> bool:
    """
    Sets all metas for a unique metadata set.

    Metas is a list of metadata id => metadata value dictionaries.

    All metas must share the same metadata set.
    """
    # prevent mixing metas from different sets
    metadatasets_ids = []
    for meta_dict in metas:
        meta = Metadata.objects.get(pk=meta_dict["id"])
        metadatasets_ids.append(meta.set.pk)
    metadatasets_ids = list(set(metadatasets_ids))
    if len(metadatasets_ids) > 1:
        raise ServiceException(NO_METADATASET_MIX)

    # check that objects exist
    resource_instance = Resource.objects.filter(
        pk=resource_id, deleted_at__isnull=True
    ).first()
    if not resource_instance:
        raise ServiceException(NO_SUCH_RESOURCE)
    metadataset_instance = MetadataSet.objects.filter(pk=metadatasets_ids[0]).first()
    if not metadataset_instance:
        raise ServiceException(NO_SUCH_METADATASET)

    # remove all metas from the set
    for meta_value in resource_instance.metadataresourcevalue_set.filter(
        metadata__set=metadataset_instance
    ):
        remove_meta_value_from_resource(user, resource_id, meta_value.pk)

    # add metas
    for meta_dict in metas:
        add_meta_to_resource(user, resource_id, meta_dict["id"], meta_dict["value"])
    resource_instance.save()  # force resource update date
    return True


@_rpc_groups(["Metadatas", "Collections"])
def set_metas_to_collection(
    user: User,
    collection_id: int,
    metas: List[dict],
    recursive: bool = False,
    async_mode: bool = True,
) -> bool:
    r"""
    Sets all metas for a unique metadata set.

    Metas is a list of metadata id => metadata value dictionaries.

    All metas must share the same metadata set.

    If recursive is True, the meta will be set to all direct children resources.

    /!\ *Not* actually recursive: Descendants (sub-collections and sub-collections resources) are IGNORED.

    async_mode is IGNORED
    """
    # prevent mixing metas from different sets
    metadatasets_ids = []
    for meta_dict in metas:
        meta = Metadata.objects.get(pk=meta_dict["id"])
        metadatasets_ids.append(meta.set.pk)
    metadatasets_ids = list(set(metadatasets_ids))
    if len(metadatasets_ids) > 1:
        raise ServiceException(NO_METADATASET_MIX)

    # check that objects exist
    collection_instance = Collection.objects.filter(
        pk=collection_id, deleted_at__isnull=True
    ).first()
    if not collection_instance:
        raise ServiceException(NO_SUCH_COLLECTION)
    metadataset_instance = MetadataSet.objects.filter(pk=metadatasets_ids[0]).first()
    if not metadataset_instance:
        raise ServiceException(NO_SUCH_METADATASET)

    # remove all metas from the set
    for meta_value in collection_instance.metadatacollectionvalue_set.filter(
        metadata__set=metadataset_instance
    ):
        remove_meta_value_from_collection(user, collection_id, meta_value.pk)

    # add metas
    for meta_dict in metas:
        add_meta_to_collection(user, collection_id, meta_dict["id"], meta_dict["value"])

    if recursive:
        user_task = UserTask.objects.create(
            owner=user,
            description=f"Applications récursives des métadonnées sur la collection {collection_instance.title}",
            project=collection_instance.project,
        )
        tasks.recursive_set_metas_to_collection(
            user.pk, collection_instance.pk, metas, user_task.pk
        )
    return True


@_rpc_groups(["Metadatas", "Resources"])
def add_meta_to_resource(
    user: User, resource_id: int, meta_id: int, meta_value: str
) -> int:
    """
    Add a meta value to a resource given their ids.
    """
    if meta_value == "" or meta_value is None:
        raise ServiceException(WRONG_ARGUMENT)
    try:
        resource_instance = Resource.objects.get(
            pk=resource_id,
            deleted_at__isnull=True,
            ptr_project__projectaccess__user=user,
            ptr_project__projectaccess__role__permissions__label=PERM_RESOURCE_READ,
        )
        # Adding a meta value to a resource is a resource.update, NOT a metadata.update.
        # No need to go further.
        _check_project_permission(
            user,
            resource_instance.ptr_project,
            PERM_RESOURCE_UPDATE,
        )
        meta = Metadata.objects.get(
            pk=meta_id,
            project__projectaccess__user=user,
            project__projectaccess__role__permissions__label=PERM_METADATA_READ,
        )
        meta_value_instance, created = MetadataResourceValue.objects.get_or_create(
            metadata=meta, resource=resource_instance, value=meta_value
        )
        return meta_value_instance.id
    except (
        Resource.DoesNotExist,
        Resource.MultipleObjectsReturned,
    ):
        raise ServiceException(NO_SUCH_RESOURCE)
    except (
        Metadata.DoesNotExist,
        Metadata.MultipleObjectsReturned,
    ):
        raise ServiceException(NO_SUCH_METADATA)


@_rpc_groups(["Metadatas", "Collections"])
def remove_meta_value_from_collection(
    user: User, collection_id: int, meta_value_id: int, recursive: bool = False
) -> bool:
    """
    Remove a meta value from a collection given their ids.
    """
    query_set: Union[Iterator[Collection], QuerySet] = Collection.objects.filter(
        pk=collection_id, deleted_at__isnull=True
    )
    collection_instance = query_set.first()
    if not collection_instance:
        raise ServiceException(NO_SUCH_COLLECTION)
    _check_project_permission(user, collection_instance.project, PERM_COLLECTION_UPDATE)
    for meta_value in collection_instance.metadatacollectionvalue_set.all():
        if meta_value.id == meta_value_id:
            meta_value.delete()
    if recursive:
        for descendant_collection_instance in collection_instance.descendants():
            remove_meta_value_from_collection(
                user, descendant_collection_instance.pk, meta_value_id
            )
        for descendant_resource_instance in collection_instance.descendants_resources():
            remove_meta_value_from_resource(
                user, descendant_resource_instance.pk, meta_value_id
            )
    return True


@_rpc_groups(["Metadatas", "Collections"])
def add_meta_to_collection(
    user: User,
    collection_id: int,
    meta_id: int,
    meta_value: str,
    recursive: bool = False,
) -> int:
    """
    Add a meta value to a collection given their ids.

    If recursive is True, the meta will be added to all descendants,
    collections and resources alike.
    """
    if meta_value == "" or meta_value is None:
        raise ServiceException(WRONG_ARGUMENT)
    try:
        collection_instance = Collection.objects.get(
            pk=collection_id,
            deleted_at__isnull=True,
            project__projectaccess__user=user,
            project__projectaccess__role__permissions__label=PERM_COLLECTION_READ,
        )
        meta = Metadata.objects.get(
            id=meta_id,
            project__projectaccess__user=user,
            project__projectaccess__role__permissions__label=PERM_METADATA_READ,
        )
        _check_project_permission(
            user,
            collection_instance.project,
            PERM_COLLECTION_UPDATE,
        )
        meta_value_instance, created = MetadataCollectionValue.objects.get_or_create(
            metadata=meta, collection=collection_instance, value=meta_value
        )
        if recursive:
            for descendant_collection in collection_instance.descendants():
                add_meta_to_collection(
                    user, descendant_collection.pk, meta_id, meta_value, False
                )
            for descendant_resource in collection_instance.descendants_resources():
                add_meta_to_resource(user, descendant_resource.pk, meta_id, meta_value)
            for resource in collection_instance.resources.filter(
                deleted_at__isnull=True
            ):
                add_meta_to_resource(user, resource.pk, meta_id, meta_value)
        return meta_value_instance.id
    except (
        Collection.DoesNotExist,
        Collection.MultipleObjectsReturned,
    ):
        raise ServiceException(NO_SUCH_COLLECTION)
    except (
        Metadata.DoesNotExist,
        Metadata.MultipleObjectsReturned,
    ):
        raise ServiceException(NO_SUCH_METADATA)


@_rpc_groups(["Metadatas", "Collections"])
def change_collection_meta_value(
    user: User, meta_value_id: int, meta_value: str
) -> bool:
    """
    Change the value of a meta for a collection.
    """
    try:
        meta_value_instance = MetadataCollectionValue.objects.get(pk=meta_value_id)
        _check_project_permission(
            user,
            meta_value_instance.metadata.project,
            PERM_COLLECTION_UPDATE,
        )
        meta_value_instance.value = meta_value
        meta_value_instance.save()
        return True
    except MetadataCollectionValue.DoesNotExist:
        return False


@_rpc_groups(["Metadatas", "Resources"])
def change_resource_meta_value(user: User, meta_value_id: int, meta_value: str) -> bool:
    """
    Change the value of a meta for a resource
    """
    try:
        meta_value_instance = MetadataResourceValue.objects.get(pk=meta_value_id)
        _check_project_permission(
            user,
            meta_value_instance.metadata.project,
            PERM_RESOURCE_UPDATE,
        )
        meta_value_instance.value = meta_value
        meta_value_instance.save()
        return True
    except MetadataResourceValue.DoesNotExist:
        return False


@_rpc_groups(["Collections"])
def ancestors_from_collection(
    user: User, collection_id: int, include_self: bool = False
) -> List[dict]:
    """
    Get ancestors from collection id as a list of serialized collections.

    If 'include_self' is true, will add the current collection at the begining.

    Example output:

    ```
    [
        {
            "id": 1,
            "title": "photos",
            "resources_count": 0,
            "children_count": 0,
            "descendants_count": 0,
            "descendants_resources_count": 0,
            "parent": null,
            "children": null,
            "metas": [],
            "public_access": false,
            "tags": [],
        },
        {
            "id": 2,
            "title": "arts",
            "resources_count": 0,
            "children_count": 0,
            "descendants_count": 0,
            "descendants_resources_count": 0,
            "parent": 1,
            "children": null,
            "metas": [],
            "public_access": false,
            "tags": [],
        },
        {
            "id": 3,
            "title": "paintings",
            "resources_count": 0,
            "children_count": 0,
            "descendants_count": 0,
            "descendants_resources_count": 0,
            "parent": 2,
            "children": null,
            "metas": [],
            "public_access": false,
            "tags": [],
        },
    ]
    ```
    """
    breadcrumb = []
    query_set: Union[Iterator[Collection], QuerySet] = Collection.objects.filter(
        pk=collection_id, deleted_at__isnull=True
    )
    collection_instance: Collection = query_set.first()
    if not collection_instance:
        raise ServiceException(NO_SUCH_COLLECTION)
    project = collection_instance.project
    _check_project_permission(user, project, PERM_COLLECTION_READ)
    if not collection_instance:
        return breadcrumb
    current_collection = collection_instance
    serializer_cache = SerializerCache()
    while True:
        if current_collection.parent:
            if (
                current_collection.parent.project == project
                and not current_collection.deleted_at
            ):
                breadcrumb.append(
                    serializers.collection(
                        current_collection.parent,
                        recursive=False,
                        cache=serializer_cache,
                    )
                )
            current_collection = current_collection.parent
        else:
            break
    breadcrumb.reverse()
    if include_self:
        breadcrumb.append(
            serializers.collection(
                collection_instance, recursive=False, cache=serializer_cache
            )
        )
    return breadcrumb


@_rpc_groups(["Collections", "Resources"])
def ancestors_from_resource(user: User, resource_id: int) -> List[List[dict]]:
    """
    Get ancestors from resource id as a list of serialized collections.

    Example output:

    ```
    [
        {
            "id": 1,
            "title": "photos",
            "resources_count": 0,
            "children_count": 0,
            "descendants_count": 0,
            "descendants_resources_count": 0,
            "parent": null,
            "children": null,
            "metas": [],
            "public_access": false,
            "tags": [],
        },
        {
            "id": 2,
            "title": "arts",
            "resources_count": 0,
            "children_count": 0,
            "descendants_count": 0,
            "descendants_resources_count": 0,
            "parent": 1,
            "children": null,
            "metas": [],
            "public_access": false,
            "tags": [],
        },
        {
            "id": 3,
            "title": "paintings",
            "resources_count": 0,
            "children_count": 0,
            "descendants_count": 0,
            "descendants_resources_count": 0,
            "parent": 2,
            "children": null,
            "metas": [],
            "public_access": false,
            "tags": [],
        },
    ]
    ```
    """
    ancestors = []
    query_set: Union[Iterator[Resource], QuerySet] = Resource.objects.filter(
        pk=resource_id, deleted_at__isnull=True
    )
    resource_instance = query_set.first()
    if not resource_instance:
        return ancestors
    project = resource_instance.ptr_project
    _check_project_permission(user, project, PERM_COLLECTION_READ)
    for collection_instance in resource_instance.collections.all():
        if (
            collection_instance.project == project
            and collection_instance.deleted_at is None
        ):
            ancestors.append(
                ancestors_from_collection(
                    user, collection_instance.id, include_self=True
                )
            )
    return ancestors


@_rpc_groups(["Collections"])
def publish_collection(user: User, collection_id: int) -> bool:
    """
    Mark a collection as public
    """
    query_set: Union[Iterator[Collection], QuerySet] = Collection.objects.filter(
        pk=collection_id, deleted_at__isnull=True
    )
    collection_instance: Collection = query_set.first()
    if not collection_instance:
        raise ServiceException(NO_SUCH_COLLECTION)
    _check_project_permission(user, collection_instance.project, PERM_COLLECTION_UPDATE)
    collection_instance.public_access = True
    collection_instance.published_at = timezone.now()
    collection_instance.save()
    return True


@_rpc_groups(["Collections"])
def unpublish_collection(user: User, collection_id: int) -> bool:
    """
    Mark a collection as private
    """
    query_set: Union[Iterator[Collection], QuerySet] = Collection.objects.filter(
        pk=collection_id, deleted_at__isnull=True
    )
    collection_instance: Collection = query_set.first()
    if not collection_instance:
        raise ServiceException(NO_SUCH_COLLECTION)
    _check_project_permission(user, collection_instance.project, PERM_COLLECTION_UPDATE)
    collection_instance.public_access = False
    collection_instance.save()
    return True


@_rpc_groups(["Collections"])
def move_collection(
    user: User, child_collection_id: int, parent_collection_id: int
) -> bool:
    """
    Move a collection from a parent to another.

    Will raise ServiceException in the following cases:

    - 'child_collection_id' and 'parent_collection_id' are equal
    - parent collection does not exist
    - parent collection is a descendant of child collection
    """
    if child_collection_id == parent_collection_id:  # no loop !
        raise ServiceException(NO_FOOTGUNS)
    query_set: Union[Iterator[Collection], QuerySet] = Collection.objects.filter(
        pk=child_collection_id, deleted_at__isnull=True
    )
    child_collection_instance: Collection = query_set.first()
    if not child_collection_instance:
        raise ServiceException(NO_SUCH_COLLECTION)

    query_set: Union[Iterator[Collection], QuerySet] = Collection.objects.filter(
        pk=parent_collection_id, deleted_at__isnull=True
    )
    parent_collection_instance: Collection = query_set.first()
    if not parent_collection_instance:
        raise ServiceException(NO_SUCH_COLLECTION)
    if parent_collection_instance in child_collection_instance.descendants():
        raise ServiceException(NO_FOOTGUNS)
    if parent_collection_instance.project_id != child_collection_instance.project_id:
        raise ServiceException(PROJECT_MISMATCH)
    _check_project_permission(
        user,
        parent_collection_instance.project,
        PERM_COLLECTION_READ,
    )
    _check_project_permission(
        user,
        child_collection_instance.project,
        PERM_COLLECTION_UPDATE,
    )
    existing_collection = Collection.objects.filter(
        project_id=parent_collection_instance.project_id,
        title=child_collection_instance.title,
        parent_id=parent_collection_instance.id,
    ).first()
    if existing_collection:
        raise ServiceException(COLLECTION_ALREADY_EXIST_IN_PARENT)
    child_collection_instance.parent = parent_collection_instance
    child_collection_instance.save()
    return True


@_rpc_groups(["Tags"])
def set_tag(
    user: User, uid: str, project_id: int, label: str = None, ark: str = None
) -> dict:
    """
    Get or create a Tag by uid (unique identifier). 'label' is an optional human-readable name.

    Example output:

    ```
    {
        "id": 1,
        "uid": "PAINTINGS",
        "label": "peintures",
        "ark": null,
    }
    ```
    """
    project = Project.objects.filter(pk=project_id).first()
    _check_project_permission(user, project, "tag.create")
    tag_instance, created = Tag.objects.get_or_create(project=project, uid=uid)
    tag_instance.ark = ark
    tag_instance.label = label
    tag_instance.save()
    return serializers.tag(tag_instance, cache=SerializerCache())


@_rpc_groups(["Tags"])
def delete_tag(user: User, uid: str) -> bool:
    """
    Remove (delete) a tag based on its uid.

    Beware: This will remove ALL associations with the tag.
    """
    try:
        tag_instance = Tag.objects.get(uid=uid)
        _check_project_permission(user, tag_instance.project, PERM_TAG_DELETE)
        tag_instance.delete()
        return True
    except Tag.DoesNotExist:
        raise ServiceException(NO_SUCH_TAG)


@_rpc_groups(["Tags"])
def tags(user: User, project_id: int) -> List[dict]:
    """
    Returns all tags available in the project.

    Example output:

    ```
    [
        {
        "id": 1,
        "uid": "PAINTINGS",
        "label": "peintures",
        "ark": null,
        },
        {
        "id": 2,
        "uid": "PHOTOS",
        "label": "photos",
        "ark": null,
        }
    ]
    ```
    """
    project = Project.objects.filter(pk=project_id).first()
    _check_project_permission(user, project, "tag.read")
    tags_list = []
    serializer_cache = SerializerCache()
    for tag_instance in Tag.objects.filter(project=project):
        tags_list.append(serializers.tag(tag_instance, cache=serializer_cache))
    return tags_list


@_rpc_groups(["Tags", "Collections"])
def add_tag_to_collection(user: User, tag_uid: str, collection_id: int) -> bool:
    """
    Add tag to a collection based on tag uid and collection id.
    """
    try:
        collection_instance = Collection.objects.get(
            pk=collection_id, deleted_at__isnull=True
        )
        project = collection_instance.project
        _check_project_permission(user, project, PERM_COLLECTION_UPDATE)
        tag_instance = Tag.objects.get(project=project, uid=tag_uid)
        collection_instance.tags.add(tag_instance)
        return True
    except Collection.DoesNotExist:
        raise ServiceException(NO_SUCH_COLLECTION)
    except Tag.DoesNotExist:
        raise ServiceException(NO_SUCH_TAG)


@_rpc_groups(["Tags", "Collections"])
def remove_tag_from_collection(user: User, tag_uid: str, collection_id: int) -> bool:
    """
    Remove tag from a collection based on tag uid and collection id.
    """
    try:
        collection_instance = Collection.objects.get(
            pk=collection_id, deleted_at__isnull=True
        )
        project = collection_instance.project
        _check_project_permission(user, project, PERM_COLLECTION_UPDATE)
        tag_instance = Tag.objects.get(project=project, uid=tag_uid)
        collection_instance.tags.remove(tag_instance)
        return True
    except Collection.DoesNotExist:
        raise ServiceException(NO_SUCH_COLLECTION)
    except Tag.DoesNotExist:
        raise ServiceException(NO_SUCH_TAG)


@_rpc_groups(["Tags", "Resources"])
def add_tag_to_resource(user: User, tag_uid: str, resource_id: int) -> bool:
    """
    Add tag to a resource based on tag uid and resource id.
    """
    try:
        resource_instance = Resource.objects.get(
            id=resource_id, deleted_at__isnull=True
        )
        project = resource_instance.ptr_project
        _check_project_permission(user, project, PERM_RESOURCE_UPDATE)
        tag_instance = Tag.objects.get(project=project, uid=tag_uid)
        resource_instance.tags.add(tag_instance)
        resource_instance.save()
        return True
    except Resource.DoesNotExist:
        raise ServiceException(NO_SUCH_RESOURCE)
    except Tag.DoesNotExist:
        raise ServiceException(NO_SUCH_TAG)


@_rpc_groups(["Tags", "Resources"])
def remove_tag_from_resource(user: User, tag_uid: str, resource_id: int) -> bool:
    """
    Remove tag from a resource based on tag uid and resource id.
    """
    try:
        resource_instance = Resource.objects.get(
            id=resource_id, deleted_at__isnull=True
        )
        project = resource_instance.ptr_project
        _check_project_permission(user, project, PERM_RESOURCE_UPDATE)
        tag_instance = Tag.objects.get(project=project, uid=tag_uid)
        resource_instance.tags.remove(tag_instance)
        resource_instance.save()
        return True
    except Resource.DoesNotExist:
        raise ServiceException(NO_SUCH_RESOURCE)
    except Tag.DoesNotExist:
        raise ServiceException(NO_SUCH_TAG)


@_rpc_groups(["Collections", "Resources"])
def set_representative_resource(
    user: User, collection_id: int, resource_id: int = None
) -> bool:
    """
    Choose a Resource that is the best representation of a collection.
    Typical use case: set a miniature for a collection.

    The Resource does not have to be contained in the collection.

    Resource id may be set set to None/Null.
    """
    try:
        collection_instance = Collection.objects.get(
            pk=collection_id, deleted_at__isnull=True
        )
        if not resource_id:
            collection_instance.representative = None
            collection_instance.save()
            return True
        resource_instance = Resource.objects.get(
            pk=resource_id, deleted_at__isnull=True
        )
        _check_project_permission(
            user,
            collection_instance.project,
            PERM_COLLECTION_UPDATE,
        )
        _check_project_permission(
            user,
            resource_instance.ptr_project,
            PERM_RESOURCE_READ,
        )
        if resource_instance.ptr_project_id == collection_instance.project_id:
            collection_instance.representative = resource_instance
            collection_instance.save()
            return True
        else:
            raise ServiceException(PROJECT_MISMATCH)
    except Collection.DoesNotExist:
        raise ServiceException(NO_SUCH_COLLECTION)
    except Resource.DoesNotExist:
        raise ServiceException(NO_SUCH_RESOURCE)


@_rpc_groups(["Utilities", "Resources"])
def replace_file(user: User, from_resource_id: int, to_resource_id: int) -> bool:
    """
    Replace a file by another using two existing resources.

    The two resources are expected to be of File type. Then the
    following operations are performed:

    - metas from the "ExifTool" set are removed from the destination resource instance
    - metas from the "ExifTool" set are transfered from the source resource instance to the destination resource instance
    - the destination resource instance gets the file hash from the source resource instance
    - the source resource instance is (hard) deleted
    - the destination resource instance is saved

    Such that all title/metas/tags/collections of the destination resource instance are untouched,
    excluding exif metas that are transfered from the source.
    """
    try:
        from_resource_instance = Resource.objects.get(
            pk=from_resource_id, deleted_at__isnull=True
        )
        if not from_resource_instance.file:
            raise ServiceException(NOT_A_FILE)
        to_resource_instance = Resource.objects.get(
            pk=to_resource_id, deleted_at__isnull=True
        )
        if not to_resource_instance.file:
            raise ServiceException(NOT_A_FILE)
        _check_project_permission(
            user,
            from_resource_instance.ptr_project,
            PERM_RESOURCE_READ,
        )
        _check_project_permission(
            user,
            to_resource_instance.ptr_project,
            PERM_RESOURCE_UPDATE,
        )
        try:
            exif_set, _ = MetadataSet.objects.get_or_create(
                title="ExifTool", project=from_resource_instance.ptr_project
            )
            # remove to_resource exif metas
            to_resource_instance.metadataresourcevalue_set.filter(
                metadata__set=exif_set
            ).delete()
            # iterate from_resource exif metas and re-affect to to_resource
            for meta_value in from_resource_instance.metadataresourcevalue_set.filter(
                metadata__set=exif_set
            ):
                meta_value.resource = to_resource_instance
                meta_value.save()
        except MetadataSet.DoesNotExist:
            pass

        # set from_resource hash and file type to to_resource hash
        to_resource_instance.file.hash = from_resource_instance.file.hash
        to_resource_instance.file.file_type = from_resource_instance.file.file_type
        to_resource_instance.file.size = from_resource_instance.file.size
        to_resource_instance.file.denormalized_image_width = (
            from_resource_instance.file.denormalized_image_width
        )
        to_resource_instance.file.denormalized_image_height = (
            from_resource_instance.file.denormalized_image_height
        )
        # delete from_resource
        from_resource_instance.delete()
        # save to_resource
        to_resource_instance.file.save()
        tasks.iiif_task(to_resource_instance.file.id)
        tasks.ocr_task(to_resource_instance.file.id)
        if to_resource_instance.ptr_project.use_exiftool:
            tasks.exif_task(to_resource_instance.file.id)
        return True
    except Resource.DoesNotExist:
        raise ServiceException(NO_SUCH_RESOURCE)


@_rpc_groups(["Access"])
@_require_superuser
def activate_rpc_access(user: User, user_name: str, api_key: str) -> bool:
    """
    Add access to the RPC API for the given user name with the given API key.
    A new user will be created if none is available with given user name.

    Requires superuser.
    """
    user_instance, _ = User.objects.get_or_create(username=user_name)
    key_instance, _ = APIKey.objects.get_or_create(user=user_instance, key=api_key)
    key_instance.active = True
    key_instance.save()
    return True


@_rpc_groups(["Access"])
@_require_superuser
def deactivate_rpc_access(user: User, user_name: str, api_key: str) -> bool:
    """
    Deactivate access to the RPC API for the given user name and API key.
    Only the access (API key) is removed, not the user.

    Requires superuser.
    """
    try:
        user_instance = User.objects.get(username=user_name)
        key_instance = APIKey.objects.get(user=user_instance, key=api_key)
        key_instance.active = False
        key_instance.save()
        return True
    except User.DoesNotExist:
        raise ServiceException(NO_SUCH_USER)
    except APIKey.DoesNotExist:
        raise ServiceException(NO_SUCH_USER)


@_rpc_groups(["Access"])
@_require_superuser
def create_project(user: User, project_label: str, project_description: str) -> dict:
    """
    Create a new project.

    Requires superuser.
    """
    project = Project.objects.create(
        label=project_label, description=project_description
    )
    return serializers.project(project, cache=SerializerCache())


@_rpc_groups(["Access"])
def list_permissions(user: User) -> List[Dict]:
    """
    Lists all available permissions in the application:

    ```
    [
        {'id': 1, 'label': 'collection.create'},
        {'id': 2, 'label': 'collection.read'},
        {'id': 3, 'label': 'collection.update'},
        {'id': 4, 'label': 'collection.delete'},
        {'id': 5, 'label': 'resource.create'},
        {'id': 6, 'label': 'resource.read'},
        {'id': 7, 'label': 'resource.update'},
        {'id': 8, 'label': 'resource.delete'},
        {'id': 9, 'label': 'metadata.create'},
        {'id': 10, 'label': 'metadata.read'},
        {'id': 11, 'label': 'metadata.update'},
        {'id': 12, 'label': 'metadata.delete'},
        {'id': 13, 'label': 'metadataset.create'},
        {'id': 14, 'label': 'metadataset.read'},
        {'id': 15, 'label': 'metadataset.update'},
        {'id': 16, 'label': 'metadataset.delete'},
        {'id': 17, 'label': 'file.create'},
        {'id': 18, 'label': 'file.read'},
        {'id': 19, 'label': 'file.update'},
        {'id': 20, 'label': 'file.delete'},
        {'id': 21, 'label': 'tag.create'},
        {'id': 22, 'label': 'tag.read'},
        {'id': 23, 'label': 'tag.update'},
        {'id': 24, 'label': 'tag.delete'},
        {'id': 25, 'label': 'file.download_source'}
    ]
    ```
    """
    data = []
    serializer_cache = SerializerCache()
    for perm in Permission.objects.all():
        data.append(serializers.permission(perm, cache=serializer_cache))
    return data


@_rpc_groups(["Access"])
def projects_user_permissions(user: User) -> List[Dict]:
    """
    Get all rights for the current user.

    Example output:

    ```
    [
        {
            'project': {'id': 7, 'label': 'john doe main project'},
            'role': {'id': 7, 'label': 'admin', 'permissions': [{"id": 1, "label": "do_anything"}]},
            'user': 'john doe'
        }
    ]
    ```
    """
    access_list = []
    serializer_cache = SerializerCache()
    for project_access in ProjectAccess.objects.filter(user=user):
        access_list.append(
            serializers.project_access(project_access, cache=serializer_cache)
        )
    return access_list


@_rpc_groups(["Access"])
def has_permission(user: User, project_id: int, permission: str) -> bool:
    """
    Test current user for given permission.
    """
    perm = ProjectAccess.objects.filter(
        user=user, project_id=project_id, role__permissions__label=permission
    ).first()
    if perm:
        return True
    return False


@_rpc_groups(["Access"])
def list_roles(user: User, project_id: int) -> List[Dict]:
    """
    Fetch all roles defined in the project, no matter the user.
    """
    _check_project_permission(user, project_id, PERM_ROLE_READ)
    data = []
    serializer_cache = SerializerCache()
    for role in Role.objects.filter(project_id=project_id):
        data.append(serializers.role(role, cache=serializer_cache))
    return data


@_rpc_groups(["Access"])
@_require_superuser
def set_role(
    user: User, project_id: int, role_label: str, permissions: List[int]
) -> Dict:
    """
    Create or update a role on a project, with the given permissions.

    Requires superuser.
    """
    project = _check_project_permission(user, project_id, PERM_PERMISSION_UPDATE)
    role, created = Role.objects.get_or_create(
        label=role_label.strip(), project=project
    )
    role.permissions.clear()
    for perm_id in permissions:
        try:
            perm = Permission.objects.get(pk=perm_id)
            role.permissions.add(perm)
        except Permission.DoesNotExist:
            pass
    return serializers.role(role, cache=SerializerCache())


@_require_superuser
@_rpc_groups(["Access"])
def delete_role(user: User, project_id: int, role_label: str) -> bool:
    """
    Delete role within given project.

    Requires superuser
    """
    Role.objects.filter(label=role_label, project_id=project_id).delete()
    return True


@_rpc_groups(["Collections", "Resources"])
def move_items(
    user: User,
    from_collection_id: int,
    to_collection_id: int,
    collections_ids: List[int],
    resources_ids: List[int],
) -> Dict[str, Dict]:
    """
    Move items (collections or resources) from one Collection to another
    """
    results = {"collections": {}, "resources": {}}
    for collection_id in collections_ids:
        try:
            results["collections"][collection_id] = move_collection(
                user, collection_id, to_collection_id
            )
        except ServiceException:
            results["collections"][collection_id] = False
    for resource_id in resources_ids:
        add_ok = add_resource_to_collection(user, resource_id, to_collection_id)
        if add_ok:
            remove_ok = remove_resource_from_collection(
                user, resource_id, from_collection_id
            )
            results["resources"][resource_id] = remove_ok
        else:
            results["resources"][resource_id] = add_ok
    return results


@_rpc_groups(["Projects"])
def project_stats(user: User, project_id: int) -> dict:
    """
    Get infos from given project:

    - id of project collection root
    - number of descendants
    - number of descendant resources
    - number of resources
    - number of children collections
    """
    try:
        project = Project.objects.get(pk=project_id)
        project_root = project.root_collection
        _check_project_permission(user, project, PERM_COLLECTION_READ)
        _check_project_permission(user, project, PERM_RESOURCE_READ)
        return {
            "project_root_collection_id": project_root.pk,
            "descendants_count": Collection.objects.filter(
                project=project, deleted_at__isnull=True
            ).count(),
            "descendants_resources_count": Resource.objects.filter(
                ptr_project=project, deleted_at__isnull=True
            ).count(),
            "children_count": Collection.objects.filter(
                project=project, deleted_at__isnull=True, parent=project_root
            ).count(),
            "resources_count": Resource.objects.filter(
                ptr_project=project,
                deleted_at__isnull=True,
                collectionmembership__isnull=True,
            ).count(),
        }
    except Project.DoesNotExist:
        raise ServiceException(NO_SUCH_PROJECT)


@_rpc_groups(["Collections", "Resources"])
def collection_stats(user: User, collection_id: int) -> dict:
    """
    Get infos from given collection:

    - number of descendants
    - number of descendant resources
    - number of resources
    - number of children collections
    """
    collection_instance = Collection.objects.filter(
        id=collection_id, deleted_at__isnull=True
    ).first()
    if not collection_instance:
        raise ServiceException(NO_SUCH_COLLECTION)
    _check_project_permission(user, collection_instance.project, PERM_COLLECTION_READ)
    return {
        "descendants_count": collection_instance.descendants_count(),
        "descendants_resources_count": collection_instance.descendant_resources_count(),
        "children_count": collection_instance.children()
        .filter(deleted_at__isnull=True)
        .count(),
        "resources_count": collection_instance.resources.filter(
            deleted_at__isnull=True
        ).count(),
    }


@_rpc_groups(["Utilities", "Collections", "Resources"])
def recycle_bin(user: User, project_id: int) -> List[Dict]:
    """
    Gets deleted elements:

    - object type
    - label
    - id
    - deleted_at
    """
    _check_project_permission(user, project_id, PERM_COLLECTION_READ)
    _check_project_permission(user, project_id, PERM_RESOURCE_READ)

    date_limit = timezone.now() - timedelta(days=15)

    results = []
    for collection_instance in Collection.objects.filter(
        deleted_at__isnull=False, project_id=project_id, deleted_at__gt=date_limit
    ).order_by("-deleted_at"):
        results.append(
            {
                "object_type": "collection",
                "id": collection_instance.pk,
                "label": collection_instance.title,
                "deleted_at": collection_instance.deleted_at.isoformat(),
            }
        )
    for resource_instance in Resource.objects.filter(
        deleted_at__isnull=False, ptr_project_id=project_id, deleted_at__gt=date_limit
    ).order_by("-deleted_at"):
        results.append(
            {
                "object_type": "resource",
                "id": resource_instance.pk,
                "label": resource_instance.title,
                "deleted_at": resource_instance.deleted_at.isoformat(),
            }
        )

    return sorted(results, key=lambda item: item.get("deleted_at"), reverse=True)


@_rpc_groups(["Resources"])
def restore_resource(
    user: User, resource_id: int, destination_collection_id: int
) -> bool:
    """
    Restore a deleted resource from the recycle bin
    """
    resource_instance = Resource.objects.filter(pk=resource_id).first()
    if not resource_instance:
        raise ServiceException(NO_SUCH_RESOURCE)
    destination_collection_instance = Collection.objects.filter(
        pk=destination_collection_id
    ).first()
    if not destination_collection_instance:
        raise ServiceException(NO_SUCH_COLLECTION)
    if resource_instance.ptr_project_id != destination_collection_instance.project_id:
        raise ServiceException(PROJECT_MISMATCH)
    _check_project_permission(user, resource_instance.ptr_project, PERM_RESOURCE_UPDATE)
    _check_project_permission(
        user,
        destination_collection_instance.project,
        PERM_COLLECTION_UPDATE,
    )
    resource_instance.deleted_at = None
    resource_instance.save()
    for old_collection in resource_instance.collections.all():
        remove_resource_from_collection(user, resource_instance.pk, old_collection.pk)
    add_resource_to_collection(
        user, resource_instance.pk, destination_collection_instance.pk
    )
    return True


@_rpc_groups(["Collections"])
def restore_collection(
    user: User, collection_id: int, destination_collection_id: int
) -> bool:
    """
    Restore a deleted collection from the recycle bin
    """
    collection_instance = Collection.objects.filter(pk=collection_id).first()
    if not collection_instance:
        raise ServiceException(NO_SUCH_COLLECTION)
    destination_collection_instance = Collection.objects.filter(
        pk=destination_collection_id
    ).first()
    if not destination_collection_instance:
        raise ServiceException(NO_SUCH_COLLECTION)
    if destination_collection_instance.project_id != collection_instance.project_id:
        raise ServiceException(PROJECT_MISMATCH)
    _check_project_permission(user, collection_instance.project, PERM_COLLECTION_UPDATE)

    def _restore(col_instance: Collection):
        col_instance.deleted_at = None
        col_instance.save()
        for resource_instance in col_instance.resource_set.filter(
            deleted_at__isnull=False
        ):
            # restore_resource(user, resource_instance.pk, col_instance.pk)
            resource_instance.deleted_at = None
            resource_instance.save()
        for child_collection_instance in Collection.objects.filter(parent=col_instance):
            _restore(child_collection_instance)

    # recurse collection, respawn all descendants
    _restore(collection_instance)
    if (
        collection_instance.parent
        and collection_instance.parent.pk != destination_collection_id
    ):
        move_collection(
            user, collection_instance.pk, destination_collection_instance.pk
        )
    return True


@_rpc_groups(["Metadatas"])
def meta_count(user: User, metadata_id: int, collection_id: int) -> dict:
    """
    Count metadata usage.
    """
    collection_instance = Collection.objects.filter(pk=collection_id).first()
    if not collection:
        raise ServiceException(NO_SUCH_COLLECTION)
    _check_project_permission(user, collection_instance.project, PERM_METADATA_READ)
    meta = Metadata.objects.filter(pk=metadata_id).first()
    if not meta:
        raise ServiceException(NO_SUCH_METADATA)
    collections_ids = collection_instance.descendants_and_self_ids()

    return_dict = {}
    meta_values = (
        MetadataResourceValue.objects.filter(
            metadata=meta, resource__collections__id__in=collections_ids
        )
        .values("value")
        .distinct()
    )

    for meta_value in meta_values:
        return_dict[meta_value["value"]] = MetadataResourceValue.objects.filter(
            metadata=meta,
            resource__collections__id__in=collections_ids,
            value=meta_value["value"],
        ).count()

    return return_dict


@_rpc_groups(["Collections"])
def public_collections(user: User, project_id: int) -> List[dict]:
    """
    Get public collections
    """
    _check_project_permission(user, project_id, PERM_COLLECTION_READ)
    data = []
    serializer_cache = SerializerCache()
    for col in Collection.objects.filter(public_access=True, project_id=project_id):
        data.append(serializers.collection(col, cache=serializer_cache))
    return data


@_rpc_groups(["Projects"])
def set_project_property(
    user: User, project_id: int, property_key: str, property_value: dict
) -> dict:
    """
    Set a property value to the project.

    property_key is NOT case sensitive, ie. "ProPertY" is the same as "pRoperTy" or "property".
    """
    _check_project_permission(user, project_id, PERM_PROJECT_PROPERTY_CREATE)
    _check_project_permission(user, project_id, PERM_PROJECT_PROPERTY_UPDATE)
    property_key = str(property_key)
    property_key = property_key.strip()
    property_key = property_key.lower()
    if not property_key or len(property_key) > 64:
        raise ServiceException(INVALID_PROPERTY_KEY)
    prop, _ = ProjectProperty.objects.update_or_create(
        project_id=project_id, key=property_key, defaults={"value": property_value}
    )
    return serializers.project_property(prop)


@_rpc_groups(["Projects"])
def delete_project_property(user: User, project_id: int, property_key: str) -> bool:
    """
    Delete a property from the project.

    property_key is NOT case sensitive, ie. "ProPertY" is the same as "pRoperTy" or "property".
    """
    _check_project_permission(user, project_id, PERM_PROJECT_PROPERTY_DELETE)
    property_key = str(property_key)
    property_key = property_key.strip()
    property_key = property_key.lower()
    if not property_key or len(property_key) > 64:
        raise ServiceException(INVALID_PROPERTY_KEY)
    prop = ProjectProperty.objects.filter(
        project_id=project_id, key=property_key
    ).first()
    if prop:
        prop.delete()
        return True
    raise ServiceException(NO_SUCH_PROJECT_PROPERTY)


@_rpc_groups(["Projects"])
def project_property(user: User, project_id: int, property_key: str) -> dict:
    """
    Get a property value from the project.

    property_key is NOT case sensitive, ie. "ProPertY" is the same as "pRoperTy" or "property".

    Will raise an exception if property does not exist.
    """
    _check_project_permission(user, project_id, PERM_PROJECT_PROPERTY_READ)
    property_key = str(property_key)
    property_key = property_key.strip()
    property_key = property_key.lower()
    if not property_key or len(property_key) > 64:
        raise ServiceException(INVALID_PROPERTY_KEY)
    prop = ProjectProperty.objects.filter(
        project_id=project_id, key=property_key
    ).first()
    if prop:
        return serializers.project_property(prop)
    raise ServiceException(NO_SUCH_PROJECT_PROPERTY)


@_rpc_groups(["Projects"])
def project_properties(user: User, project_id: int) -> List[dict]:
    """
    Get ALL properties from a project.
    """
    _check_project_permission(user, project_id, PERM_PROJECT_PROPERTY_READ)
    data = []
    for prop in ProjectProperty.objects.filter(project_id=project_id):
        data.append(serializers.project_property(prop))
    return data


@_rpc_groups(["Resources"])
def picture_rotate_crop(
    user: User,
    resource_id: int,
    rotation: float = 0,
    top_crop: int = 0,
    right_crop: int = 0,
    bottom_crop: int = 0,
    left_crop: int = 0,
) -> dict:
    """
    Rotate and crop an image. The resulting image then replaces the
    original in the current resource.

    Will return the resource upon success. Throws a ServiceException
    otherwise.
    """
    file_instance = File.objects.filter(pk=resource_id, deleted_at__isnull=True).first()
    if not file_instance:
        raise ServiceException(NO_SUCH_RESOURCE)
    _check_project_permission(user, file_instance.project, PERM_RESOURCE_UPDATE)
    if not file_instance.file:
        raise ServiceException(NOT_A_FILE)
    if not file_instance.file.should_have_iiif:
        raise ServiceException(NOT_AN_IMAGE)
    try:
        top_crop = int(top_crop)
        right_crop = int(right_crop)
        bottom_crop = int(bottom_crop)
        left_crop = int(left_crop)
        rotation = float(rotation)
        if rotation > 360 or rotation < 0:
            raise ValueError
    except ValueError:
        raise ServiceException(WRONG_ARGUMENT)
    if rotation + top_crop + right_crop + bottom_crop + left_crop == 0:
        raise ServiceException(NOTHING_TO_DO)
    tmp_pic_path = "{}/resize-{}-{}-{}-{}-{}-{}{}".format(
        settings.TMP_THUMBNAILS_DIR,
        file_instance.pk,
        rotation,
        top_crop,
        right_crop,
        bottom_crop,
        left_crop,
        file_instance.original_name_extension,
    )
    try:
        pyvips.cache_set_max(0)
        img = pyvips.Image.new_from_file(file_instance.local_path())
        if rotation:
            img = img.rotate(rotation)
        img = img.extract_area(
            left_crop,
            top_crop,
            img.width - left_crop - right_crop,
            img.height - top_crop - bottom_crop,
        )
        img.write_to_file(tmp_pic_path)
        new_file_id = _handle_local_file(tmp_pic_path, file_instance.project)
        _set_exif_metas(new_file_id)
        if not replace_file(user, new_file_id, resource_id):
            raise ServiceException(UNKNOWN_ERROR)
        os.remove(tmp_pic_path)
        return serializers.file(File.objects.get(pk=resource_id), include_metas=True)
    except pyvips.error.Error as pyvips_error:
        logger.warning(pyvips_error)
        raise ServiceException(CANT_CREATE_IMAGE)


def _find_items_sets_from_selection_dict(
    from_collection_id: int, selection: dict
) -> Tuple[QuerySet[Resource], QuerySet[Collection]]:
    """
    Will find child items of parent collection based on criterias given in selection,
    such as these:

    ```
    {
        "include": {
            "resources_ids": [3493, 159]
            "collections_ids:" [20, 31]
        },
        "exclude": {
            "resources_ids": [12, 10, 15]
            "collections_ids:" [4, 254, 17]
        }
    }
    ```
    If no include, all items from parent are selected and then excludes are applied.

    """
    if not selection:
        selection = {}
    if not from_collection_id:
        raise ServiceException(NO_SUCH_COLLECTION)
    parent_collection = Collection.objects.filter(pk=from_collection_id).first()
    if not parent_collection:
        raise ServiceException(NO_SUCH_COLLECTION)

    # Par défaut, tout sélectionner depuis la collec parente
    children_collections_set = parent_collection.children()
    resources_set = parent_collection.resources.all()

    if selection.get("include"):
        # Si liste d'inclusion... ne rien sélectionner par défaut
        children_collections_set = Collection.objects.none()
        resources_set = Resource.objects.none()
        if selection["include"].get("collections_ids"):
            children_collections_set = Collection.objects.filter(
                id__in=selection["include"].get("collections_ids")
            )
        if selection["include"].get("resources_ids"):
            resources_set = Resource.objects.filter(
                id__in=selection["include"].get("resources_ids")
            )

    # Appliquer les exclusions sur les query set précédents
    if selection.get("exclude"):
        if selection["exclude"].get("collections_ids"):
            children_collections_set = children_collections_set.exclude(
                id__in=selection["exclude"].get("collections_ids")
            )
        if selection["exclude"].get("resources_ids"):
            resources_set = resources_set.exclude(
                id__in=selection["exclude"].get("resources_ids")
            )

    return resources_set, children_collections_set


@_rpc_groups(["Resources", "Collections"])
def remove_selection(user: User, parent_collection_id: int, selection: dict) -> bool:
    """
    Will mass remove items (resources AND collections) based on parent collection

    Use such an object for inclusion/exclusion:

    ```
    {
        "include": {
            "resources_ids": [3493, 159]
            "collections_ids:" [20, 31]
        },
        "exclude": {
            "resources_ids": [12, 10, 15]
            "collections_ids:" [4, 254, 17]
        }
    }
    ```

    deleteCollection (with recursion) and deleteResource are used under the hood.

    The parent collection is left as-is.
    """

    res_set, children_collections_set = _find_items_sets_from_selection_dict(
        parent_collection_id, selection
    )

    for collection_instance in children_collections_set.all():
        delete_collection(user, collection_instance.id, True)

    for resource_instance in res_set.all():
        # is resource anywhere else ?
        if resource_instance.collections.filter(deleted_at__isnull=True).count() < 2:
            delete_resource(user, resource_instance.id)
        else:
            remove_resource_from_collection(
                user, resource_instance.id, parent_collection_id
            )
    return True


@_rpc_groups(["Resources", "Collections"])
def move_selection(
    user: User, from_collection_id: int, selection: dict, to_collection_id: int
) -> Dict[str, Dict]:
    """
    Will mass move items (resources AND collections) based on parent collection and destination collection

    Use such an object for inclusion/exclusion:

    ```
    {
        "include": {
            "resources_ids": [3493, 159]
            "collections_ids:" [20, 31]
        },
        "exclude": {
            "resources_ids": [12, 10, 15]
            "collections_ids:" [4, 254, 17]
        }
    }
    ```
    """

    resources_set, children_collections_set = _find_items_sets_from_selection_dict(
        from_collection_id, selection
    )

    recipient_collection = Collection.objects.filter(pk=to_collection_id).first()
    if not recipient_collection:
        raise ServiceException(NO_SUCH_COLLECTION)

    # we only need ids to use move_items
    collections_ids = []
    for collection_instance in children_collections_set.all():
        collections_ids.append(collection_instance.id)
    resources_ids = []
    for resource_instance in resources_set.all():
        resources_ids.append(resource_instance.id)

    return move_items(
        user,
        from_collection_id,
        recipient_collection.id,
        collections_ids,
        resources_ids,
    )


@_rpc_groups(["Resources", "Collections"])
def add_meta_to_selection(
    user: User, from_collection_id: int, selection: dict, meta_id: int, meta_value: str
) -> bool:
    """
    Use such a dict for selection:
    ```
    {
        "include": {
            "resources_ids": [3493, 159]
            "collections_ids:" [20, 31]
        },
        "exclude": {
            "resources_ids": [12, 10, 15]
            "collections_ids:" [4, 254, 17]
        }
    }
    ```
    """
    resources_set, collections_set = _find_items_sets_from_selection_dict(
        from_collection_id, selection
    )
    for resource_instance in resources_set.filter(deleted_at__isnull=True):
        add_meta_to_resource(user, resource_instance.pk, meta_id, meta_value)
    for collection_instance in collections_set.filter(deleted_at__isnull=True):
        add_meta_to_collection(
            user, collection_instance.pk, meta_id, meta_value, True
        )  # cascading
    return True


@_rpc_groups(["Resources", "Collections"])
def remove_meta_value_from_selection(
    user: User, from_collection_id: int, selection: dict, meta_value_id: int
) -> bool:
    """
    Use such a dict for selection:
    ```
    {
        "include": {
            "resources_ids": [3493, 159]
            "collections_ids:" [20, 31]
        },
        "exclude": {
            "resources_ids": [12, 10, 15]
            "collections_ids:" [4, 254, 17]
        }
    }
    ```
    """
    resources_set, collections_set = _find_items_sets_from_selection_dict(
        from_collection_id, selection
    )
    for resource_instance in resources_set.all():
        remove_meta_value_from_resource(user, resource_instance.pk, meta_value_id)
    for collection_instance in collections_set.all():
        remove_meta_value_from_collection(
            user, collection_instance.pk, meta_value_id, True
        )
    return True


@_rpc_groups(["Resources"])
def auto_find_rotate_angle(user: User, resource_id: int) -> float:
    """
    Tries to determine skew angle of image with text.
    """
    resource_instance = Resource.objects.filter(pk=resource_id).first()
    if not resource_instance:
        raise ServiceException(NO_SUCH_RESOURCE)
    if not resource_instance.file:
        raise ServiceException(NOT_A_FILE)
    if not resource_instance.file.should_have_iiif:
        raise ServiceException(NOT_AN_IMAGE)
    return _deskew(resource_instance.file.local_path())


@_rpc_groups(["Resources"])
def update_resource_from_xlsx_row(user: User, resource_data: dict) -> bool:
    """
    Compound method to update resource and resources metadata from a xlsx file row.
    """
    resource_instance = Resource.objects.filter(
        pk=resource_data.get("pk"), deleted_at__isnull=True
    ).first()
    if not resource_instance:
        raise ServiceException(NO_SUCH_RESOURCE)
    _check_project_permission(user, resource_instance.ptr_project, PERM_RESOURCE_UPDATE)
    new_title = resource_data.get("title", "").strip()
    if new_title:
        resource_instance.title = new_title

    for k in resource_data.keys():
        if ":" in k:  # example: Dublin Core: creator
            meta_set_name, meta_name = [x.strip() for x in k.split(":")]
            metadata_instance = Metadata.objects.filter(
                title=meta_name, set__title=meta_set_name
            ).first()
            if metadata_instance:
                MetadataResourceValue.objects.filter(
                    metadata=metadata_instance, resource=resource_instance
                ).delete()
                if resource_data.get(k) is not None:
                    for value in [
                        x.strip()
                        for x in str(resource_data.get(k, "")).split(
                            XLSX_MULTIPLE_VALUES_SEPARATOR
                        )
                    ]:
                        meta_resource_value = MetadataResourceValue()
                        meta_resource_value.resource = resource_instance
                        meta_resource_value.metadata = metadata_instance
                        meta_resource_value.value = value.strip()
                        meta_resource_value.save()
    resource_instance.save()  # force update of resource
    return True


@_rpc_groups(["Resources"])
def user_tasks_status(user: User, project_id: int = None) -> List[dict]:
    """
    Returns list of user tasks. Each task being serialized like so:

    ```
    {
        "object_type": "task",
        "id": user_task_instance.id,
        "description": user_task_instance.description,
        "created_at": user_task_instance.created_at.isoformat(),
        "started_at": user_task_instance.started_at.isoformat(),
        "finished_at": user_task_instance.finished_at.isoformat(),
        "failed_at": user_task_instance.failed_at.isoformat(),
        "project_id": user_task_instance.project_id
    }
    ```
    """
    out = []
    q = UserTask.objects.filter(owner=user)
    if project_id is not None:
        q = q.filter(project_id=project_id)
    for user_task in q:
        out.append(serializers.user_task(user_task))
    return out


def _serialize_annotation(annotation: Annotation) -> dict:
    return {
        "id": annotation.id,
        "owner": annotation.owner.username,
        "data": annotation.data,
        "created_at": annotation.created_at.isoformat(),
        "updated_at": annotation.updated_at.isoformat(),
        "resource_id": annotation.resource_id,
        "public": annotation.public,
    }


def _fetch_resource(resource_id: int) -> Resource:
    resource_instance = Resource.objects.filter(
        pk=resource_id, deleted_at__isnull=True
    ).first()
    if not resource_instance:
        raise ServiceException(NO_SUCH_RESOURCE)
    return resource_instance


@_rpc_groups(["Annotations"])
def list_annotations(user: User, resource_id: int) -> List[dict]:
    """
    List all annotations for a given resource
    """
    resource_instance = _fetch_resource(resource_id)
    _check_project_permission(user, resource_instance.ptr_project, PERM_RESOURCE_READ)
    annotations_list = []
    for annotation in Annotation.objects.filter(resource=resource_instance).order_by(
        "created_at"
    ):
        annotations_list.append(_serialize_annotation(annotation))
    return annotations_list


@_rpc_groups(["Annotations"])
def list_collection_annotations(user: User, collection_id: int) -> List[dict]:
    """
    List all annotations for a given collection
    """
    collection_instance = Collection.objects.filter(pk=collection_id).first()
    if not collection_instance:
        raise ServiceException("no such collection")
    _check_project_permission(user, collection_instance.project, PERM_RESOURCE_READ)
    resources_list = []
    for resource_instance in collection_instance.available_resources():
        serialized_resource = serializers.resource(
            resource_instance, include_metas=False
        )
        serialized_resource["annotations"] = []
        for annotation in Annotation.objects.filter(
            resource=resource_instance
        ).order_by("created_at"):
            serialized_resource["annotations"].append(_serialize_annotation(annotation))
        resources_list.append(serialized_resource)
    return resources_list


@_rpc_groups(["Annotations"])
def create_annotation(
    user: User, resource_id: int, data: dict, public: bool = False
) -> dict:
    """
    Adds an annotation, returning the serialized annotation:

    ```
    {
        "id": annotation.id,
        "owner": annotation.owner.username,
        "data": annotation.data,
        "created_at": annotation.created_at.isoformat(),
        "updated_at": annotation.updated_at.isoformat(),
        "resource_id": annotation.resource_id,
        "public": annotation.public
    }
    ```
    """
    resource_instance = _fetch_resource(resource_id)
    _check_project_permission(user, resource_instance.ptr_project, PERM_RESOURCE_UPDATE)
    annotation = Annotation.objects.create(
        resource=resource_instance, owner=user, data=data, public=public
    )
    return _serialize_annotation(annotation)


@_rpc_groups(["Annotations"])
def update_annotation(
    user: User, annotation_id: int, data: dict, public: bool = False
) -> dict:
    """
    Updates an annotation, returning the serialized annotation
    """
    annotation_instance = Annotation.objects.filter(pk=annotation_id).first()
    if not annotation_instance:
        raise ServiceException("No such annotation")
    _check_project_permission(
        user, annotation_instance.resource.ptr_project, PERM_RESOURCE_UPDATE
    )
    annotation_instance.data = data
    annotation_instance.public = public
    annotation_instance.save()
    return _serialize_annotation(annotation_instance)


@_rpc_groups(["Annotations"])
def delete_annotation(user: User, annotation_id: int) -> bool:
    """
    Deletes an annotation
    """
    annotation_instance = Annotation.objects.filter(pk=annotation_id).first()
    if not annotation_instance:
        raise ServiceException("No such annotation")
    _check_project_permission(
        user, annotation_instance.resource.ptr_project, PERM_RESOURCE_UPDATE
    )
    annotation_instance.delete()
    return True


@_rpc_groups(["Annotations"])
def publish_annotation(user: User, annotation_id: int) -> bool:
    annotation_instance = Annotation.objects.filter(pk=annotation_id).first()
    if not annotation_instance:
        raise ServiceException("No such annotation")
    _check_project_permission(
        user, annotation_instance.resource.ptr_project, PERM_RESOURCE_UPDATE
    )
    annotation_instance.public = True
    annotation_instance.save()
    return True


@_rpc_groups(["Annotations"])
def unpublish_annotation(user: User, annotation_id: int) -> bool:
    annotation_instance = Annotation.objects.filter(pk=annotation_id).first()
    if not annotation_instance:
        raise ServiceException("No such annotation")
    _check_project_permission(
        user, annotation_instance.resource.ptr_project, PERM_RESOURCE_UPDATE
    )
    annotation_instance.public = False
    annotation_instance.save()
    return True
