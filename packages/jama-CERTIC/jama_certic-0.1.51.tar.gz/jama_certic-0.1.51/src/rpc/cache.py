from resources import models
from django.contrib.auth.models import User


class SerializerCache:
    def __init__(self):
        self._cache_dict = {}

    def fetch_obj(self, obj_type: str, obj_id: int):
        cache_key = "{}{}".format(obj_type, obj_id)
        if cache_key not in self._cache_dict.keys():
            if obj_type == "metadata":
                self._cache_dict[cache_key] = models.Metadata.objects.get(pk=obj_id)
            elif obj_type == "metadataset":
                self._cache_dict[cache_key] = models.MetadataSet.objects.get(pk=obj_id)
            elif obj_type == "user":
                self._cache_dict[cache_key] = User.objects.get(pk=obj_id)
            elif obj_type == "project":
                self._cache_dict[cache_key] = models.Project.objects.get(pk=obj_id)
            elif obj_type == "role":
                self._cache_dict[cache_key] = models.Role.objects.get(pk=obj_id)
            elif obj_type == "file_type":
                self._cache_dict[cache_key] = models.FileType.objects.get(pk=obj_id)
            else:
                raise ValueError("unsupported object type: {}".format(obj_type))
        return self._cache_dict.get(cache_key)
