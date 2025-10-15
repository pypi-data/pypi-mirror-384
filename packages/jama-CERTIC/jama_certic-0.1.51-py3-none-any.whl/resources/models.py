from django.utils.text import slugify
from django.db import models, connection
from django.contrib.auth.models import User
import os
from jama import settings
import hashlib
from typing import Iterator, Union, List
from django.db.models.signals import post_save
from django.dispatch import receiver
from subprocess import call
from django.utils.timezone import now
from resources import tasks
import pytesseract
import logging
from PIL import Image, UnidentifiedImageError
from functools import cache
from django.db.models.query import QuerySet

Image.MAX_IMAGE_PIXELS = None

XLSX_MULTIPLE_VALUES_SEPARATOR = "\n--\n"

logger = logging.getLogger(__name__)


def _flatten_resource(
    resource: "Resource", known_metadatas: dict, metadatas_labels: List
) -> dict:
    data = {"pk": resource.pk, "title": resource.title}
    metadata_ids = known_metadatas.keys()
    for known_metadata_label in metadatas_labels:
        data[known_metadata_label] = None
    for mr in (
        resource.metadataresourcevalue_set.exclude(metadata__title="ExifTool")
        .exclude(metadata__title="OCR")
        .exclude(metadata__title="scd_cms")
        .select_related("metadata")
    ):
        if mr.metadata.pk in metadata_ids:
            meta_key = f"{str(mr.metadata)}"
            if data[meta_key]:
                data[meta_key] = (
                    data[meta_key] + XLSX_MULTIPLE_VALUES_SEPARATOR + mr.value
                )
            else:
                data[meta_key] = mr.value
    return data


def hash_to_iiif_path(file_hash: str, separator: str = os.path.sep) -> str:
    return "{}{}{}{}{}".format(
        file_hash[:2], separator, file_hash[2:4], separator, file_hash
    )


def hash_to_local_path(file_hash: str) -> str:
    return "{}{}{}{}{}{}{}".format(
        settings.MEDIA_FILES_DIR.rstrip("/"),
        os.path.sep,
        file_hash[:2],
        os.path.sep,
        file_hash[2:4],
        os.path.sep,
        file_hash,
    )


def hash_to_iiif_thumbnail_url(
    file_hash: str, width: int = None, height: int = None
) -> str:
    return "{}{}/full/{}{},{}/0/default.jpg".format(
        settings.JAMA_IIIF_ENDPOINT,
        hash_to_iiif_path(file_hash, settings.IIIF_PATH_SEPARATOR),
        settings.JAMA_IIIF_UPSCALING_PREFIX,
        width or "",
        height or "",
    )


def hash_to_iiif_manifest(file_hash: str) -> str:
    iiif_path = hash_to_iiif_path(file_hash, settings.IIIF_PATH_SEPARATOR)
    return "{}{}/info.json".format(settings.JAMA_IIIF_ENDPOINT, iiif_path)


class NotIIIF(RuntimeError):
    pass


class APIKey(models.Model):
    key = models.CharField("clef", max_length=40, unique=True)
    active = models.BooleanField("actif", default=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return "{}: {}".format(self.user, self.key)

    class Meta:
        verbose_name = "clef d'API"
        verbose_name_plural = "clefs d'API"
        unique_together = (("key", "user"),)


class Project(models.Model):
    """
    Project is used for sharing collections
    and resources between users.
    """

    label = models.TextField(unique=True)
    description = models.TextField()
    admin_mail = models.EmailField(null=True)
    #
    # Intended as a redirect pattern for ark resolving.
    # Example: https://service.tld/ark/redirect/[CLASS]/[ARK].
    #
    # Replaced values are:
    # - [CLASS]: "resource" or "collection"
    # - [ARK]: ARK name (Resource.ark or Collection.ark)
    # - [PK]: Resource.pk or Collection.pk
    #
    # See jama.views.ark_resource and jama.views.ark_collection.
    #
    ark_redirect = models.TextField(null=True)
    # Exiftool returns a lot of data and you may not need it in your
    # project. When set to false, the exiftool task is bypassed.
    use_exiftool = models.BooleanField(default=False)

    def __str__(self):
        return self.label

    @property
    def root_collection(self) -> "Collection":
        if not hasattr(self, "_cached_root_collection"):
            try:
                col, created = Collection.objects.get_or_create(
                    project=self, parent=None
                )
                if created:
                    col.title = "root {}".format(self.label)
                    col.save()
            except Collection.MultipleObjectsReturned:
                col = Collection.objects.filter(project=self, parent=None).first()
            self._cached_root_collection = col
        return self._cached_root_collection

    def metadatas(self, exclude_automatic_metas=True) -> List["Metadata"]:
        metadatas = []
        query = MetadataSet.objects.filter(project=self).order_by("title")
        if exclude_automatic_metas:
            query = query.exclude(title="ExifTool").exclude(title="OCR")
        for metadataset in query.iterator():
            for metadata in (
                Metadata.objects.filter(set=metadataset).order_by("title").iterator()
            ):
                metadatas.append(metadata)
        return metadatas


class ProjectProperty(models.Model):
    """
    Generic key/value store for the project.

    Store anything that is needed by the client application,
    like user prefs, field labels or other useful data.

    Be extra careful with access rights here.
    """

    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    key = models.CharField(max_length=128, null=False, blank=False)
    value = models.JSONField()

    class Meta:
        unique_together = (("project", "key"),)


class UserTask(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    started_at = models.DateTimeField(null=True)
    finished_at = models.DateTimeField(null=True)
    failed_at = models.DateTimeField(null=True)
    canceled_at = models.DateTimeField(null=True)
    project = models.ForeignKey(Project, null=True, on_delete=models.CASCADE)

    class Meta:
        ordering = ["-updated_at"]


class Tag(models.Model):
    uid = models.TextField()
    ark = models.TextField(null=True, blank=True)
    label = models.TextField(null=True, blank=True)  # pref label de SKOS
    project = models.ForeignKey(Project, on_delete=models.CASCADE)

    def __str__(self):
        return self.label or self.uid

    class Meta:
        verbose_name = "étiquette"
        verbose_name_plural = "étiquettes"
        unique_together = (("uid", "project"),)


class FileExtension(models.Model):
    label = models.CharField("extension", max_length=32, unique=True)

    def __str__(self):
        return ".{}".format(self.label)

    class Meta:
        verbose_name = "extension de fichier"
        verbose_name_plural = "extensions de fichier"


class FileType(models.Model):
    title = models.TextField("titre")
    mime = models.CharField("type MIME", max_length=128, unique=True)
    extensions = models.ManyToManyField(FileExtension)
    serve_with_iiif = models.BooleanField("Servir par IIIF", default=False)

    def __str__(self):
        return "{}".format(self.title)

    class Meta:
        verbose_name = "type de fichier"
        verbose_name_plural = "types de fichier"


@cache
def _file_type_is_served_with_iiif(file_type_id: int) -> bool:
    return FileType.objects.get(pk=file_type_id).serve_with_iiif


class MetadataSet(models.Model):
    title = models.TextField("titre")
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "{}".format(self.title)

    class Meta:
        verbose_name = "Groupe de meta-données"
        verbose_name_plural = "Groupes de meta-données"
        unique_together = (("title", "project"),)


class Metadata(models.Model):
    title = models.TextField("titre")
    set = models.ForeignKey(MetadataSet, on_delete=models.CASCADE)
    rank = models.IntegerField("ordre", default=0)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    expose = models.BooleanField(default=True)

    def __str__(self):
        return "{}: {}".format(self.set.title, self.title)

    class Meta:
        verbose_name = "meta-donnée"
        verbose_name_plural = "meta-données"
        unique_together = (("title", "set", "project"),)
        ordering = ["set", "rank", "title"]


class Resource(models.Model):
    title = models.TextField("titre")
    collections = models.ManyToManyField("Collection", through="CollectionMembership")
    tags = models.ManyToManyField(Tag)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    # this is duplicated as "project" at the File class level
    # to enforce a unique constraint on Project and File hash.
    # "ptr" stands for "pointer" since the Resource class should
    # not be used directly.
    ptr_project = models.ForeignKey(Project, on_delete=models.CASCADE, null=True)
    ark = models.CharField("nom ARK", max_length=64, null=True)

    def __str__(self):
        return "{}".format(self.title)

    class Meta:
        verbose_name = "ressource"
        verbose_name_plural = "ressources"
        ordering = ("title",)

    def soft_delete(self):
        self.deleted_at = now()
        self.save()

    def available_collections(self) -> Iterator["Collection"]:
        return self.collections.filter(deleted_at__isnull=True).iterator()


class File(Resource):
    original_name = models.TextField("nom d'origine")
    # this duplicates "ptr_project" from Resource class
    # (can't have unique constraints across tables unfortunately)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    hash = models.CharField("hachage", max_length=64)
    file_type = models.ForeignKey(FileType, on_delete=models.RESTRICT)
    size = models.BigIntegerField("taille")
    # shortcuts
    denormalized_image_width = models.IntegerField(
        "largeur de l'image", blank=True, null=True
    )
    denormalized_image_height = models.IntegerField(
        "hauteur de l'image", blank=True, null=True
    )
    text_boxes = models.JSONField("text boxes de tesseract", blank=True, null=True)
    tiled = models.BooleanField(default=False)

    def __str__(self):
        return "{}".format(self.title)

    def hash_is_ok(self) -> bool:
        from resources.helpers import _file_hash256

        return _file_hash256(self.local_path()) == self.hash

    @property
    def should_have_iiif(self) -> bool:
        return _file_type_is_served_with_iiif(self.file_type_id)

    def image_width(self) -> Union[int, None]:
        if self.denormalized_image_width is None:
            self.denormalized_image_width = self.image_width_from_metas()
        return self.denormalized_image_width

    def image_height(self) -> Union[int, None]:
        if self.denormalized_image_height is None:
            self.denormalized_image_height = self.image_height_from_metas()
        return self.denormalized_image_height

    def image_width_from_metas(self) -> Union[int, None]:
        val = None
        if self.should_have_iiif:
            if self.project.use_exiftool:
                prop = self.metadataresourcevalue_set.filter(
                    metadata__title__iendswith="imagewidth",
                    metadata__set__title__iexact="exiftool",
                ).first()
                if prop:
                    try:
                        val = int(prop.value)
                    except ValueError:
                        pass
            else:
                try:
                    image = Image.open(self.local_path())
                    val, _ = image.size
                except (UnidentifiedImageError, FileNotFoundError):
                    logger.warning(
                        f"Could not get width for file({self.pk}) using PIL. Possible image corruption."
                    )
        return val

    def image_height_from_metas(self) -> Union[int, None]:
        val = None
        if self.should_have_iiif:
            if self.project.use_exiftool:
                prop = self.metadataresourcevalue_set.filter(
                    metadata__title__iendswith="imageheight",
                    metadata__set__title__iexact="exiftool",
                ).first()
                if prop:
                    try:
                        val = int(prop.value)
                    except ValueError:
                        pass
            else:
                try:
                    image = Image.open(self.local_path())
                    _, val = image.size
                except (UnidentifiedImageError, FileNotFoundError):
                    logger.warning(
                        f"Could not get height for file({self.pk}) using PIL. Possible image corruption."
                    )
        return val

    class Meta:
        verbose_name = "fichier"
        verbose_name_plural = "fichiers"
        unique_together = (("project", "hash"),)

    def filter_meta(self, full_meta_title: str, default_value=None):
        """
        Simple access to wanted meta. ":" is used as a separator.

        Ex:
            some_file.filter_meta("ExifTool:ID3:Album", "")
        """
        full_meta_title = full_meta_title.lower()
        for metaval in self.metadataresourcevalue_set.all():
            current_meta_title = "{}:{}".format(
                metaval.metadata.set.title, metaval.metadata.title
            ).lower()
            if current_meta_title == full_meta_title:
                return metaval.value
        return default_value

    def iiif_infos_url(self) -> str:
        if self.should_have_iiif:
            return "{}{}/info.json".format(
                settings.JAMA_IIIF_ENDPOINT,
                hash_to_iiif_path(self.hash, settings.IIIF_PATH_SEPARATOR),
            )
        else:
            raise NotIIIF("Resource is not served via IIIF")

    @property
    def iiif_m_thumbnail_url(self) -> str:
        return self.iiif_thumbnail_url(300)

    @property
    def iiif_s_thumbnail_url(self) -> str:
        return self.iiif_thumbnail_url(100)

    @property
    def iiif_xs_thumbnail_url(self) -> str:
        return self.iiif_thumbnail_url(50)

    def iiif_thumbnail_url(self, width: int = None, height: int = None) -> str:
        if self.should_have_iiif:
            return "{}{}/full/{}{},{}/0/default.jpg".format(
                settings.JAMA_IIIF_ENDPOINT,
                hash_to_iiif_path(self.hash, settings.IIIF_PATH_SEPARATOR),
                settings.JAMA_IIIF_UPSCALING_PREFIX,
                width or "",
                height or "",
            )
        else:
            raise NotIIIF("Resource is not served via IIIF")

    def local_path(self):
        return hash_to_local_path(self.hash)

    def ocr_output(self) -> Union[None, str]:
        """
        Fetch OCR output if available. None if not available.
        """
        metas_set, created = MetadataSet.objects.get_or_create(
            title="OCR", project=self.project
        )
        meta, created = Metadata.objects.get_or_create(
            title="tesseract output", set=metas_set, project=self.project
        )
        try:
            meta_value = MetadataResourceValue.objects.get(metadata=meta, resource=self)
            return meta_value.value
        except MetadataResourceValue.DoesNotExist:
            return None

    def make_ocr(self, refresh: bool = False):
        """
        Performs OCR on file if OCR output not yet available.
        Use refresh = True to force OCR.
        """
        if not self.should_have_iiif:  # not a picture
            return
        if self.ocr_output() and not refresh:
            return

        try:
            im = Image.open(self.local_path())
            content = pytesseract.image_to_string(im)
            ocr_metas_set, _ = MetadataSet.objects.get_or_create(
                title="OCR", project=self.project
            )
            tesseract_meta, _ = Metadata.objects.get_or_create(
                project=self.project, title="tesseract output", set=ocr_metas_set
            )
            MetadataResourceValue.objects.filter(
                metadata=tesseract_meta, resource=self
            ).delete()
            MetadataResourceValue.objects.get_or_create(
                metadata=tesseract_meta, resource=self, value=content.strip()
            )
            boxes = pytesseract.image_to_boxes(im, output_type=pytesseract.Output.DICT)
            self.text_boxes = boxes
            self.save()
        except UnidentifiedImageError:
            pass

        if self.has_extension("pdf") or self.has_extension("ai"):
            # extract PDF text layer if available
            pdftotext_return_code = call(
                [
                    "pdftotext",
                    self.local_path(),
                    self.local_path() + ".pdftotext.txt",
                ]
            )
            if pdftotext_return_code == 0:
                with open(self.local_path() + ".pdftotext.txt", "r") as text_layer:
                    content = text_layer.read()
                    metas_set, _ = MetadataSet.objects.get_or_create(
                        title="OCR", project=self.project
                    )
                    meta, _ = Metadata.objects.get_or_create(
                        project=self.project, title="pdftotext output", set=metas_set
                    )
                    MetadataResourceValue.objects.filter(
                        metadata=meta, resource=self
                    ).delete()
                    MetadataResourceValue.objects.get_or_create(
                        metadata=meta, resource=self, value=content.strip()
                    )

    def has_extension(self, extension: str) -> bool:
        extension = extension.lower()
        for ext in self.file_type.extensions.all():
            if ext.label == extension:
                return True
        return False

    def save(self, *args, **kwargs):
        self.ptr_project = self.project
        super(File, self).save(*args, **kwargs)

    @property
    def new_filename(self) -> str:
        """
        Get new filename computed from title.
        Tries to keep original extension.
        """
        _, extension = os.path.splitext(self.original_name)
        if not extension:
            extension = "." + self.file_type.extensions.first().label
        base_name, _ = os.path.splitext(self.title)
        slugged_title = slugify(base_name)
        return slugged_title + extension.lower()

    @property
    def original_name_extension(self) -> str:
        _, ext = os.path.splitext(self.original_name)
        return ext


class Collection(models.Model):
    title = models.TextField("titre")
    resources = models.ManyToManyField(Resource, through="CollectionMembership")
    tags = models.ManyToManyField(Tag)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, null=True)
    parent = models.ForeignKey("self", null=True, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    public_access = models.BooleanField("accès public", default=False)
    published_at = models.DateTimeField(null=True, blank=True)
    # Used to mark a resource as representative of a collection.
    # Typical use case: set a miniature for a collection
    representative = models.ForeignKey(
        "Resource",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="represents",
    )
    ark = models.CharField("nom ARK", max_length=64, null=True)

    def __str__(self):
        return "{}".format(self.title)

    @property
    def iiif_m_thumbnail_url(self) -> Union[str, None]:
        if (
            self.representative
            and self.representative.file
            and self.representative.file.should_have_iiif
        ):
            return self.representative.file.iiif_m_thumbnail_url
        return None

    def ark_destination_url(self) -> str:
        if self.ark and self.project.ark_redirect:
            return self.project.ark_redirect.replace("[CLASS]", "collection").replace(
                "[PK]", self.pk
            )
        return ""

    def ancestors(self) -> List["Collection"]:
        ancestors = []
        parent = self.parent
        while parent:
            ancestors.append(parent)
            parent = parent.parent
        ancestors.reverse()
        return ancestors

    def children(self) -> QuerySet["Collection"]:
        return Collection.objects.filter(parent=self, deleted_at__isnull=True).order_by(
            "title"
        )

    def available_resources(self) -> QuerySet[Resource]:
        return (
            self.resources.filter(deleted_at__isnull=True)
            .order_by("collectionmembership__rank", "title")
            .select_related("file")
        )

    def descendants(self) -> Iterator["Collection"]:
        yield from _recurse_collection(self)

    def descendants_resources(self) -> Iterator[Resource]:
        for res in (
            self.resources.filter(deleted_at__isnull=True)
            .order_by("collectionmembership__rank", "title")
            .iterator()
        ):
            yield res
        for col in _recurse_collection(self):
            for res in (
                col.resources.filter(deleted_at__isnull=True)
                .order_by("collectionmembership__rank", "title")
                .iterator()
            ):
                yield res

    def descendants_and_self_ids(self) -> List[int]:
        ids = [self.pk]
        for descendant in self.descendants():
            ids.append(descendant.pk)
        return ids

    def descendants_count(self) -> int:
        if settings.JAMA_SQLITE_DB_PATH:
            return sum(1 for _ in self.descendants())
        else:
            with connection.cursor() as cursor:
                cursor.execute(
                    """select count(*)
                    from resources_collection
                    where id = any(get_all_collection_descendants_array(%s))
                    and deleted_at is null;""",
                    [self.id],
                )
                row = cursor.fetchone()
                return int(row[0])

    def descendants_resources_count(self) -> int:
        """
        This counts resources from all the descendant collections,
        EXCLUDING the current collection's direct resources.
        """
        if settings.JAMA_SQLITE_DB_PATH:
            total = 0
            for col in self.descendants():
                total = total + col.resources.filter(deleted_at__isnull=True).count()
            return total
        else:
            with connection.cursor() as cursor:
                # For some reason, Postgresql will perform a fast index scan when given the list of collection ids as
                # a string literal in an ANY clause. When given directly the procedure's result (list of int values),
                # it will perform a slow sequential scan. Solution: Prepare a string literal.

                # FIRST, get all descendants ids
                cursor.execute(
                    """select array_agg(id)
                from resources_collection
                where id = any(get_all_collection_descendants_array(%s))
                and deleted_at is null;""",
                    [self.id],
                )
                row = cursor.fetchone()
                if not row[0]:
                    return 0
                cursor.execute(
                    """select count(*) from resources_collectionmembership
                    inner join resources_resource on resources_collectionmembership.resource_id = resources_resource.id
                    where collection_id = any({})
                    and deleted_at is null;""".format(
                        # THEN, make the string literal.
                        # (TODO: write a procedure so PGSQL can make the literal string by itself)
                        "'{" + ",".join(str(x) for x in row[0]) + "}'"
                    ),
                )
                row = cursor.fetchone()
                return int(row[0])

    def descendant_resources_count(self) -> int:
        """
        This counts descendant resources INCLUDING the current collection's direct resources.
        """
        return (
            self.descendants_resources_count()
            + self.resources.filter(deleted_at__isnull=True).count()
        )

    class Meta:
        verbose_name = "collection"
        verbose_name_plural = "collections"
        unique_together = (("title", "project", "parent"),)
        ordering = ("title",)

    def soft_delete(self):
        self.deleted_at = now()
        self.save()

    def dublin_core_metas(self) -> List["MetadataCollectionValue"]:
        metas = []
        try:
            dublin_core_set = MetadataSet.objects.get(
                title__iexact="Dublin Core", project=self.project
            )
            for metadata in self.metadatacollectionvalue_set.filter(
                metadata__set=dublin_core_set
            ).iterator():
                metas.append(metadata)
            return metas
        except MetadataSet.DoesNotExist:
            return []

    def dublin_core_title(self) -> str:
        dc_metas = self.dublin_core_metas()
        for m in dc_metas:
            if m.metadata.title == "title":
                return m.value
        return self.title

    def to_path(self):
        titles = []
        for ancestor in self.ancestors():
            titles.append(ancestor.title)
        titles.append(self.title)
        return titles

    def yield_resource_data_for_export(self) -> Iterator[dict]:
        known_metadatas = {}
        known_metadatas_labels = []
        for metadata in self.project.metadatas():
            known_metadatas[metadata.pk] = metadata
            known_metadatas_labels.append(f"{str(metadata)}")

        # for res in (
        #    self.resources.filter(deleted_at__isnull=True)
        #    .order_by("title")
        #    .prefetch_related("metadataresourcevalue_set")
        # ):
        #    yield _flatten_resource(res, known_metadatas, known_metadatas_labels)
        for res in self.descendants_resources():
            yield _flatten_resource(res, known_metadatas, known_metadatas_labels)


def _recurse_collection(collection: Collection) -> Iterator[Collection]:
    try:
        for child in collection.children().iterator():
            yield child
            yield from _recurse_collection(child)
    except RecursionError:
        pass


class MetadataCollectionValue(models.Model):
    metadata = models.ForeignKey(Metadata, on_delete=models.CASCADE)
    collection = models.ForeignKey(Collection, on_delete=models.CASCADE)
    value = models.TextField()
    sha1digest = models.CharField(max_length=40, null=False, blank=False, unique=True)

    def save(self, *args, **kwargs):
        self.sha1digest = hashlib.sha1(
            "{}-{}-{}".format(self.metadata_id, self.collection_id, self.value).encode()
        ).hexdigest()
        super(MetadataCollectionValue, self).save(*args, **kwargs)


class MetadataResourceValue(models.Model):
    metadata = models.ForeignKey(Metadata, on_delete=models.CASCADE)
    resource = models.ForeignKey(Resource, on_delete=models.CASCADE)
    value = models.TextField()
    sha1digest = models.CharField(max_length=40, null=False, blank=False, unique=True)

    def save(self, *args, **kwargs):
        self.sha1digest = hashlib.sha1(
            "{}-{}-{}".format(self.metadata_id, self.resource_id, self.value).encode()
        ).hexdigest()
        super(MetadataResourceValue, self).save(*args, **kwargs)

    class Meta:
        ordering = ("metadata",)


class CollectionMembership(models.Model):
    resource = models.ForeignKey(Resource, on_delete=models.CASCADE)
    collection = models.ForeignKey(Collection, on_delete=models.CASCADE)
    rank = models.IntegerField("ordre", default=0)

    def __str__(self):
        return "{} <-> {}".format(self.collection.title, self.resource.title)

    class Meta:
        verbose_name = "ressource <-> collection"
        verbose_name_plural = "ressources <-> collections"
        unique_together = (("resource", "collection"),)


class Permission(models.Model):
    """
    Format labels like so: [object type].[action]

    Permissions are NOT project-specific, they are
    tied to the API.

    Examples:
        - collection.delete
        - resource.add
        - meta.modify
        - resource.move
    and so on...
    """

    label = models.TextField(unique=True)

    def __str__(self):
        return self.label


class Role(models.Model):
    label = models.TextField()
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    permissions = models.ManyToManyField(Permission)

    def __str__(self):
        return self.label

    class Meta:
        unique_together = (("label", "project"),)


class ProjectAccess(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    role = models.ForeignKey(Role, on_delete=models.CASCADE)

    def __str__(self):
        return "{}: {} ({})".format(self.project, self.user, self.role)

    class Meta:
        unique_together = (("project", "user", "role"),)


@receiver(post_save, sender=Resource)
def resource_post_save(sender, instance: Resource, **kwargs):  # noqa
    if not instance.ark:
        tasks.set_ark_to_resource(instance.pk)


@receiver(post_save, sender=File)
def file_post_save(sender, instance: File, **kwargs):  # noqa
    if not instance.ark:
        tasks.set_ark_to_resource(instance.pk)


@receiver(post_save, sender=Collection)
def collection_post_save(sender, instance: Collection, **kwargs):  # noqa
    tasks.set_ark_to_collection(instance.pk)
