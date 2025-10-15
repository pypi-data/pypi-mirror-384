from django.core.management.base import BaseCommand
from inspect import signature
from rpc.views import _get_rpc_methods

all_methods = _get_rpc_methods()

TPL = '''
@_rpc_groups({})
def jama_{}{}:
    """
    {}
    """
    _jama_api_key = APIKey.objects.filter(user=user).first()
    try:
        jama = JamaClient(settings.ATLAS_JAMA_RPC_ENDPOINT, _jama_api_key.key)
        return jama.{}({})
    except JamaServiceError as e:
        raise ServiceException(e.message)
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
                .replace("user: django.contrib.auth.models.User", "user: User")
                .replace("NoneType", "None")
            )
            print(
                TPL.format(
                    all_methods.get(key).rpc_groups,
                    key,
                    shortened_signature,
                    all_methods.get(key).__doc__.strip(),
                    key,
                    ", ".join(keep_params),
                )
            )
