from functools import cache
from .parser import Parser, parser
from .parse_result import ParseResult
from .parse_context import ParseContext
from pyforma._util import defaulted


@cache
def _non_empty[T](in_parser: Parser[T], /, *, name: str) -> Parser[T]:
    @parser(name=name)
    def parse_non_empty(context: ParseContext) -> ParseResult[T]:
        r = in_parser(context)
        if r.context == context:
            return ParseResult.make_failure(expected=name, context=context)
        return r

    return parse_non_empty


def non_empty[T](in_parser: Parser[T], /, *, name: str | None = None) -> Parser[T]:
    """Creates a parser that behaves like the provided parser but fails on empty matches

    Args:
        in_parser: The base parser
        name: Optionally, the name of the parser

    Returns:
        Composed parser
    """

    name = defaulted(name, f"non-empty({in_parser.name})")

    return _non_empty(in_parser, name=name)
