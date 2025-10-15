from django.core.management.base import BaseCommand
from resources.models import File
from resources.tasks import iiif_task
from resources.helpers import iiif_destination_dir_from_hash
import os
from django.utils import timezone


class Command(BaseCommand):
    def handle(self, *args, **options):
        start_date = timezone.now() - timezone.timedelta(days=1)
        for f in File.objects.filter(
            file_type__serve_with_iiif=True,
            deleted_at__isnull=True,
            created_at__gte=start_date,
        ).distinct():
            iiif_destination_dir = iiif_destination_dir_from_hash(f.hash)
            iiif_destination_file = "{}{}".format(iiif_destination_dir, f.hash)
            if not os.path.exists(iiif_destination_file):
                iiif_task(f.pk)
