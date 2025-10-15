from django.core.management.base import BaseCommand
from inspect import signature
import re
from rpc.views import _get_rpc_methods

all_methods = _get_rpc_methods()
under_pat = re.compile(r"_([a-z])")


def underscore_to_camel(name):
    return under_pat.sub(lambda x: x.group(1).upper(), name)


PARAM_TPL = "     * @param {} {}"
RETURN_TPL = "     * @returns {}"
FN_TPL = """
    /**
{}
     */
    async {}({}) {{
        return this._rpc("{}", [{}]);
    }}
"""


types_trans = {
    "<class 'str'>": "{String}",
    "<class 'int'>": "{BigInteger}",
    "<class 'bool'>": "{Boolean}",
    "<class 'float'>": "{Number}",
    "typing.List[typing.Dict]": "{Array}",
    "typing.Dict": "{Object}",
    "typing.Optional[typing.Dict]": "{Object}",
    "typing.Dict[str, typing.List]": "{Object}",
    "typing.List[dict]": "{Array}",
    "typing.List[str]": "{Array}",
    "typing.List[int]": "{Array}",
    "typing.List[typing.List[dict]]": "{Array}",
    "typing.Union[int, bool]": "{Any}",
    "typing.Union[typing.Dict, NoneType]": "{Any}",
    "<class 'dict'>": "{Object}",
    "typing.Optional[int]": "{BigInteger|null}",
    "typing.Optional[str]": "{String|null}",
    "typing.Dict[str, typing.Dict]": "{Object}",
}

param_trans = {
    "False": "false",
    "True": "true",
    "None": "null",
    "0": "0",
    "2000": "2000",
    "title": '"title"',
}


def _add_stars(str_in: str) -> str:
    str_in = str_in or ""
    out = ""
    for line in str_in.split("\n")[1:]:
        out = out + "     * " + line[4:] + "\n"
    return "     " + out.strip()


class Command(BaseCommand):
    def handle(self, *args, **options):
        for key in sorted(all_methods.keys()):
            doc_block = _add_stars(all_methods.get(key).__doc__)
            sign = signature(all_methods.get(key))
            rpc_params = []
            sign_params = []
            for param in list(sign.parameters.items())[1:]:
                doc_block = (
                    doc_block
                    + "\n"
                    + PARAM_TPL.format(types_trans[str(param[1].annotation)], param[0])
                )
                rpc_params.append(param[0])
                if str(param[1].default) == "<class 'inspect._empty'>":
                    sign_params.append(param[0])
                else:
                    sign_params.append(
                        "{} = {}".format(param[0], param_trans[str(param[1].default)])
                    )
            doc_block = (
                doc_block
                + "\n"
                + RETURN_TPL.format(types_trans[str(sign.return_annotation)])
            )
            print(
                FN_TPL.format(
                    doc_block,
                    underscore_to_camel(key),
                    ", ".join(sign_params),
                    key,
                    ", ".join(rpc_params),
                )
            )
