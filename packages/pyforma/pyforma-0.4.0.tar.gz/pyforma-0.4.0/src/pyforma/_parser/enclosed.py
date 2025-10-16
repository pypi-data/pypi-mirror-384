from functools import cache

from .sequence import sequence
from .parser import Parser
from pyforma._util import defaulted


@cache
def _enclosed[T, U](
    *, delim: Parser[T], content: Parser[U], name: str
) -> Parser[tuple[T, U, T]]:
    return sequence(delim, content, delim, name=name)


def enclosed[T, U](
    *,
    delim: Parser[T],
    content: Parser[U],
    name: str | None = None,
) -> Parser[tuple[T, U, T]]:
    """Creates a parser for content enclosed on the left and right

    Args:
        delim: Parser for the delimiter
        content: Parser for the content
        name: Optional parser name

    Returns:
        The composed parser.
    """

    name = defaulted(name, f"enclosed({delim.name}, {content.name})")

    return _enclosed(delim=delim, content=content, name=name)
