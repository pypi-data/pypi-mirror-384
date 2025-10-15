from django.core.management.base import BaseCommand, CommandError
from resources.models import Project, File
import os
from django.utils.text import slugify


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("destination_dir", type=str)

    def handle(self, *args, **options):
        destination_dir = options.get("destination_dir").rstrip("/")
        if not os.path.isdir(destination_dir):
            raise CommandError("{} is not a directory".format(destination_dir))

        for project in Project.objects.all():
            for f in File.objects.filter(project=project):
                for col in f.collections.all():
                    normalized_names = [
                        destination_dir,
                        "{}-{}".format(project.label, project.pk),
                    ]
                    for dir in col.to_path():
                        normalized_names.append(slugify(dir))
                    full_dir_path = "/".join(normalized_names)
                    fname, _ = os.path.splitext(f.title)
                    full_file_path = (
                        os.path.join(full_dir_path, slugify(fname))
                        + "."
                        + f.file_type.extensions.first().label
                    )
                    os.makedirs(full_dir_path, exist_ok=True)
                    try:
                        os.symlink(f.local_path(), full_file_path)
                    except FileExistsError:
                        pass
                    print(full_file_path)
