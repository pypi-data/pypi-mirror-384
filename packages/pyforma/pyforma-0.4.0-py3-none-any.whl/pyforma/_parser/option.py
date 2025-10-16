from functools import cache

from .parse_result import ParseResult
from .parse_context import ParseContext
from .parser import Parser, parser
from pyforma._util import defaulted


@cache
def _option[T](in_parser: Parser[T], /, *, name: str) -> Parser[T | None]:
    @parser(name=name)
    def parse_option(context: ParseContext) -> ParseResult[T | None]:
        r = in_parser(context)
        if r.is_failure:
            return ParseResult.make_success(context=context, result=None)
        return r

    return parse_option


def option[T](in_parser: Parser[T], /, *, name: str | None = None) -> Parser[T | None]:
    """Creates a parser that behaves like the provided parser but returns an empty match on failure

    Args:
        in_parser: The base parser
        name: Optional parser name

    Returns:
        Composed parser
    """

    name = defaulted(name, f"option({in_parser.name})")

    return _option(in_parser, name=name)
