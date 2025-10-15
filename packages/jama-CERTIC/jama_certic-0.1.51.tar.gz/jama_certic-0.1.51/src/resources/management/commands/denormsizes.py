from django.core.management.base import BaseCommand
from resources.models import File
from PIL import UnidentifiedImageError
from PIL.Image import DecompressionBombError


class Command(BaseCommand):
    def handle(self, *args, **options):
        for file in File.objects.filter(
            denormalized_image_height__isnull=True,
            denormalized_image_width__isnull=True,
        ):
            try:
                if (
                    file.denormalized_image_width is None
                    and file.denormalized_image_height is None
                ):
                    x = file.image_width()
                    y = file.image_height()
                    if x and y:
                        file.save()
                    else:
                        print(f"can't find x and y for {file.pk}")
            except UnidentifiedImageError:
                print(f"can't identify {file.pk}")
            except DecompressionBombError:
                print(f"can't decompress {file.pk}")
