from django.core.management.base import BaseCommand
from inspect import signature
from rpc.views import _get_rpc_methods

all_methods = _get_rpc_methods()

TPL = '''def {}{}:
    """
    {}
    """
    return self.__call("{}", [{}])
'''


class Command(BaseCommand):
    def handle(self, *args, **options):
        for key in sorted(all_methods.keys()):
            sign = signature(all_methods.get(key))
            keep_params = []
            for param in list(sign.parameters.items())[1:]:
                keep_params.append(param[0])
            shortened_signature = (
                str(sign)
                .replace("user: django.contrib.auth.models.User", "self")
                .replace("NoneType", "None")
            )
            print(
                TPL.format(
                    key,
                    shortened_signature,
                    all_methods.get(key).__doc__.strip(),
                    key,
                    ", ".join(keep_params),
                )
            )
