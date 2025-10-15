from django.core.management.base import BaseCommand
from django.conf import settings
import os
import time
import shutil


class Command(BaseCommand):
    def handle(self, *args, **options):
        now = time.time()
        max_age = 60 * 60 * 24
        sub_folders = [
            f.path for f in os.scandir(settings.PARTIAL_UPLOADS_DIR) if f.is_dir()
        ]
        for folder in sub_folders:
            folder_time = os.path.getmtime(folder)
            if now - folder_time > max_age:
                shutil.rmtree(folder)
