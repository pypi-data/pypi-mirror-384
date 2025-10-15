import os
from django.core.management.base import BaseCommand, CommandError
from fuse import FUSE, FuseOSError, Operations
import errno
from resources.models import Collection, Resource, slugify, File
from jama import settings
from functools import lru_cache
import time


def get_ttl_hash(seconds=3600):
    """Return the same value withing `seconds` time period"""
    return round(time.time() / seconds)


@lru_cache(maxsize=1024)
def _db_obj_from_path(path: str, ttl_hash=None):
    """
    For fast access, paths should include objects pk:

    ex_collection-2/other_col-23/more_col-43/some_pic-374.jpg
    """
    last_item = path.rstrip("/").split("/")[-1]
    if last_item:
        name, ext = os.path.splitext(last_item)
        pk = name.split("-")[-1]
        try:
            pk = int(pk)
        except ValueError:
            return
        if not ext:
            return Collection.objects.filter(pk=pk).first()
        else:
            return Resource.objects.filter(pk=pk).first()
    return


class Ops(Operations):
    def __init__(self, root_collection: Collection):
        self.root_collection = root_collection

    def _obj_from_path(self, path: str):
        """
        For fast access, paths should include objects pk:

        ex_collection-2/other_col-23/more_col-43/some_pic-374.jpg
        """
        if path == "/":
            return self.root_collection
        obj = _db_obj_from_path(path, ttl_hash=get_ttl_hash())
        if not obj:
            raise FuseOSError(errno.ENOENT)
        else:
            return obj

    def _collection_fs_name(self, collection: Collection) -> str:
        return f"{slugify(collection.title)}-{collection.pk}"

    def _file_fs_name(self, file: File) -> str:
        return (
            f"{slugify(file.title)}-{file.pk}.{file.file_type.extensions.first().label}"
        )

    # Filesystem methods

    def access(self, path, mode):
        """
        modes:

        0 -> no access
        1 -> execution
        2 -> write
        4 -> read
        """
        # we want a read-only file system,
        # with execution for dirs
        if mode in [2]:
            raise FuseOSError(errno.EACCES)
        obj = self._obj_from_path(path)
        if type(obj) is Resource and mode == 1:
            raise FuseOSError(errno.EACCES)

    def chmod(self, path, mode):
        # no use in read-only fs
        raise FuseOSError(errno.EACCES)

    def chown(self, path, uid, gid):
        # no use in read-only fs
        raise FuseOSError(errno.EACCES)

    def getattr(self, path, fh=None):
        obj = self._obj_from_path(path=path)
        if type(obj) is Resource:
            if obj.file:
                st = os.lstat(obj.file.local_path())
                return dict(
                    (key, getattr(st, key))
                    for key in (
                        "st_atime",
                        "st_ctime",
                        "st_gid",
                        "st_mode",
                        "st_mtime",
                        "st_nlink",
                        "st_size",
                        "st_uid",
                    )
                )
        if type(obj) is Collection:
            st = os.lstat(settings.MEDIA_FILES_DIR)
            st_dict = dict(
                (key, getattr(st, key))
                for key in (
                    "st_atime",
                    "st_ctime",
                    "st_gid",
                    "st_mode",
                    "st_mtime",
                    "st_nlink",
                    "st_size",
                    "st_uid",
                )
            )
            return st_dict
        raise FuseOSError(errno.ENOENT)

    def readdir(self, path: str, fh):
        collection: Collection = self._obj_from_path(path=path)
        for res in collection.resources.filter(deleted_at__isnull=True):
            if res.file:
                yield self._file_fs_name(res.file)
        for col in collection.children().filter(deleted_at__isnull=True):
            yield self._collection_fs_name(col)

    def readlink(self, path):
        # no symlinks in Jama
        raise FuseOSError(errno.EACCES)

    def mknod(self, path, mode, dev):
        # no use in read-only fs
        raise FuseOSError(errno.EACCES)

    def rmdir(self, path):
        # no use in read-only fs
        raise FuseOSError(errno.EACCES)

    def mkdir(self, path, mode):
        # no use in read-only fs
        raise FuseOSError(errno.EACCES)

    def statfs(self, path):
        # Using MEDIA_FILES_DIR as all Jama File resources are located there
        stv = os.statvfs(settings.MEDIA_FILES_DIR)
        return dict(
            (key, getattr(stv, key))
            for key in (
                "f_bavail",
                "f_bfree",
                "f_blocks",
                "f_bsize",
                "f_favail",
                "f_ffree",
                "f_files",
                "f_flag",
                "f_frsize",
                "f_namemax",
            )
        )

    def unlink(self, path):
        # no use in read-only fs
        raise FuseOSError(errno.EACCES)

    def symlink(self, name, target):
        # no use in read-only fs
        raise FuseOSError(errno.EACCES)

    def rename(self, old, new):
        # no use in read-only fs
        raise FuseOSError(errno.EACCES)

    def link(self, target, name):
        # no use in read-only fs
        raise FuseOSError(errno.EACCES)

    def utimens(self, path, times=None):
        raise FuseOSError(errno.EACCES)

    # File methods
    # ============

    def open(self, path, flags):
        if flags != os.O_RDONLY:
            raise FuseOSError(errno.EACCES)
        f = self._obj_from_path(path=path)
        if not f:
            raise FuseOSError(errno.ENOENT)
        if type(f) is not Resource:
            raise FuseOSError(errno.ENOENT)
        if not f.file:
            raise FuseOSError(errno.ENOENT)
        return os.open(f.file.local_path(), os.O_RDONLY)

    def create(self, path, mode, fi=None):
        # no use in read-only fs
        raise FuseOSError(errno.EACCES)

    def read(self, path, length, offset, fh):
        os.lseek(fh, offset, os.SEEK_SET)
        return os.read(fh, length)

    def write(self, path, buf, offset, fh):
        # no use in read-only fs
        raise FuseOSError(errno.EACCES)

    def truncate(self, path, length, fh=None):
        # no use in read-only fs
        raise FuseOSError(errno.EACCES)

    def flush(self, path, fh):
        # no use in read-only fs
        raise FuseOSError(errno.EACCES)

    def release(self, path, fh):
        # no use in read-only fs
        raise FuseOSError(errno.EACCES)

    def fsync(self, path, fdatasync, fh):
        # no use in read-only fs
        raise FuseOSError(errno.EACCES)


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("mount_point", type=str)
        parser.add_argument("root_collection", type=int)

    def handle(self, *args, **options):
        mount_point = options.get("mount_point")
        if not os.path.isdir(mount_point):
            raise CommandError(f"{mount_point} is not a directory")
        root_collection_id = options.get("root_collection")
        root_collection = Collection.objects.filter(pk=root_collection_id).first()
        if not root_collection:
            raise CommandError(f"{root_collection_id} is not a valid collection id")
        FUSE(
            Ops(root_collection),
            mount_point,
            nothreads=True,
            foreground=True,
            allow_other=True,
        )
