from django.core.management.base import BaseCommand
from django.db import connection
from resources.helpers import make_iiif
from concurrent.futures import ProcessPoolExecutor


def tile_file(pk: int):
    try:
        make_iiif(pk, True)
        print(pk)
    except Exception as e:
        print(e)
        raise e


class Command(BaseCommand):
    def handle(self, *args, **options):
        pks = []
        cursor = connection.cursor()
        cursor.execute(
            "select resource_ptr_id from resources_file where resources_file.tiled = false order by resource_ptr_id"
        )
        for row in cursor.fetchall():
            pks.append(row[0])
        connection.close()
        with ProcessPoolExecutor(max_workers=10) as executor:
            for pk in pks:
                executor.submit(tile_file, pk)
