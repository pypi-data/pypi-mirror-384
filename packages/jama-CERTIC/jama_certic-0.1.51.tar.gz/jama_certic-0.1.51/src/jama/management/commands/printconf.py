from django.core.management.base import BaseCommand
from django.conf import settings
from pathlib import Path


class Command(BaseCommand):
    def handle(self, *args, **options):
        for k in sorted(dir(settings)):
            if k.upper() == k:
                val = getattr(settings, k)
                if type(val) in [str, Path, bool, int, None]:
                    print(f"{k}: {val}")
