from django.http import (
    HttpRequest,
    HttpResponseNotFound,
    HttpResponseBadRequest,
    FileResponse,
)
import pyvips
from resources.models import File
import os.path
from typing import Union
from jama import settings


def simple_thumb(
    request: HttpRequest, sha256: str, size: int
) -> Union[FileResponse, HttpResponseNotFound, HttpResponseBadRequest]:
    pic_file = File.objects.filter(hash=sha256).first()
    if not pic_file:
        return HttpResponseNotFound("Not Found")
    if not pic_file.should_have_iiif:
        return HttpResponseNotFound("Not Found")
    tmp_pic_path = "{}/simple_thumb-{}-{}.jpg".format(
        settings.TMP_THUMBNAILS_DIR, sha256, size
    )
    if not os.path.isfile(tmp_pic_path):
        thumbnail = pyvips.Image.thumbnail(
            pic_file.local_path(),
            int(size),  # crop="attention"
        )
        thumbnail.write_to_file(tmp_pic_path)
    return FileResponse(open(tmp_pic_path, "rb"))


def thumb(
    request: HttpRequest, sha256: str, angle: float, scale: float, crop: str
) -> Union[FileResponse, HttpResponseNotFound, HttpResponseBadRequest]:
    pic_file = File.objects.filter(hash=sha256).first()
    if not pic_file:
        return HttpResponseNotFound("Not Found")
    try:
        top, right, bottom, left = crop.split(",")
        top = int(top)
        right = int(right)
        bottom = int(bottom)
        left = int(left)
        angle = float(angle)
        scale = float(scale)
        if angle > 360 or angle < 0 or scale < 0 or scale > 1:
            raise ValueError
    except ValueError:
        return HttpResponseBadRequest("Bad Request")
    tmp_pic_path = "{}/thumb-{}-{}-{}-{}-{}-{}-{}.jpg".format(
        settings.TMP_THUMBNAILS_DIR, sha256, angle, scale, top, right, bottom, left
    )
    if not os.path.isfile(tmp_pic_path):
        crop_color = [96]
        pyvips.cache_set_max(0)
        img = pyvips.Image.new_from_file(pic_file.local_path())
        if angle:
            img = img.rotate(angle)
        img = img.draw_rect(crop_color, 0, 0, left, img.height, fill=True)
        img = img.draw_rect(crop_color, 0, 0, img.width, top, fill=True)
        img = img.draw_rect(
            crop_color, 0, img.height - bottom, img.width, bottom, fill=True
        )
        img = img.draw_rect(
            crop_color, img.width - right, 0, right, img.height, fill=True
        )
        img = img.resize(scale)
        img.write_to_file(tmp_pic_path)
    return FileResponse(open(tmp_pic_path, "rb"))
