from collections.abc import Callable
from functools import cache

from .parse_context import ParseContext
from .parse_result import ParseResult
from .parser import Parser, parser


@cache
def munch(
    predicate: Callable[[str], bool],
    /,
    *,
    name: str | None = None,
) -> Parser[str]:
    """Creates a parser that consumes the maximal prefix for which the predicate returns True

    Args:
        predicate: Predicate that determines parsed prefix
        name: Optional name for the parser

    Returns:
        A parser that consumes the maximal prefix for which the predicate returns True. The predicate is only called for
        non-empty prefixes. If no non-empty prefix passes the predicate, the parser returns an empty match.
    """

    if name is None:
        name = "munch"
        if hasattr(predicate, "__name__"):
            name = predicate.__name__
        elif hasattr(predicate, "__class__"):
            name = predicate.__class__.__name__

    @parser(name=name)
    def parse_munching(context: ParseContext) -> ParseResult[str]:
        return _munch_impl(context, predicate)

    return parse_munching


def _munch_impl(
    source: ParseContext,
    predicate: Callable[[str], bool],
) -> ParseResult[str]:
    remaining = source
    offset = 0
    while not remaining.at_eof():
        if predicate(source.peek(offset + 1)):
            offset += 1
            remaining = remaining.consume()
        else:
            break
    return ParseResult.make_success(context=remaining, result=source.peek(offset))
