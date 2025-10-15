import markdown2
from django import template
from inspect import signature
from rpc.views import _get_rpc_methods

all_methods = _get_rpc_methods()
register = template.Library()


def infer_json_type(py_type: str) -> str:
    py_type = py_type.strip()
    types = {
        "int": "number",
        "float": "number",
        "list": "array",
        "dict": "object",
        "str": "string",
        "None": "null",
        "List[dict]": "array[object]",
        "List[Dict]": "array[object]",
        "bool": "boolean",
        "Union[int, bool]": "number | boolean",
        "Dict[str, List]": "object",
        "List[str]": "array[string]",
        "List[List[dict]]": "array[object]",
        "Optional[Dict]": "object | null",
        "False": "false",
        "True": "true",
        "Dict": "object",
    }
    return types.get(py_type, py_type)


@register.filter(name="doc_string")
def doc_string(fn_name: str) -> str:
    doc = all_methods[fn_name].__doc__
    if not doc:
        return "No documentation available"
    ds = doc.strip()
    return markdown2.markdown(ds)


@register.filter(name="returntype")
def arguments(fn_name):
    sign = signature(all_methods[fn_name])
    try:
        _, return_type = str(sign).split("->")
    except ValueError:
        return_type = None
    return infer_json_type(return_type.strip() if return_type else "")


@register.filter(name="parameters")
def parameters(fn_name):
    out = ""
    sign = signature(all_methods[fn_name])
    shortened_signature = (
        str(sign)
        .replace("user: django.contrib.auth.models.User,", "")
        .replace("user: django.contrib.auth.models.User ", "")
        .replace("user: django.contrib.auth.models.User", "")
        .replace("NoneType", "None")
        .replace("(", "")
        .replace(")", "")
    ).strip()
    params = shortened_signature.split("->")[0]
    for param in params.split(","):
        param = param.strip()
        if not param:
            continue
        try:
            param_name, param_type = param.split(":")
        except ValueError:
            param_name = param
            param_type = ""
        try:
            param_type, param_default = param_type.split("=")
        except ValueError:
            param_default = None

        out = out + "<li><strong>{}</strong> ({}{})</li>".format(
            param_name.strip(),
            infer_json_type(param_type.strip()),
            (
                " <em> defaults to " + infer_json_type(param_default) + "</em>"
                if param_default
                else ""
            ),
        )
    if not out:
        return "<em>no parameters</em>"
    return "<ul>{}</ul>".format(out)


@register.filter(name="rpc_groups_from_function")
def rpc_groups_from_function(fn_name: str) -> str:
    fn = all_methods[fn_name]
    return " ".join(getattr(fn, "rpc_groups", []))


@register.filter(name="rpc_groups_as_list")
def rpc_groups_as_list(fns) -> list:
    groups = []
    for _, fn in fns:
        grps = getattr(fn, "rpc_groups", [])
        for group in grps:
            groups.append(group)
    return list(set(groups))
