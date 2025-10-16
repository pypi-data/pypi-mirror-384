from functools import cache

from .literal import literal
from .until import not_in
from .parser import Parser
from pyforma._util import defaulted


@cache
def text(*end_strs: str, name: str | None = None) -> Parser[str]:
    """Creates a parser of unstructured text

    Args:
        end_strs: syntax indicators that end unstructured text
        name: Optional parser name

    Returns:
        A parser for unstructured text
    """

    name = defaulted(name, f"text({', '.join(end_strs)})")

    return not_in(*(literal(s) for s in end_strs), name=name)
