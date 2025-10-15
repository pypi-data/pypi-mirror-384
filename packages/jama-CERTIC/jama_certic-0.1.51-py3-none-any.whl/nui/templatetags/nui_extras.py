from django import template
from functools import cache

register = template.Library()


@register.simple_tag
@cache
def jama_version() -> str:
    import jama

    return jama.__version__
