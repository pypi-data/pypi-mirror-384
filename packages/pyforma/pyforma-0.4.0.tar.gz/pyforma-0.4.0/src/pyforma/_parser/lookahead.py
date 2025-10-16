from functools import cache
from .parser import Parser, parser
from .parse_result import ParseResult
from .parse_context import ParseContext
from pyforma._util import defaulted


@cache
def _lookahead[T](in_parser: Parser[T], /, *, name: str) -> Parser[None]:
    @parser(name=name)
    def parse_lookahead(context: ParseContext) -> ParseResult[None]:
        r = in_parser(context)
        if r.is_success:
            return ParseResult.make_success(context=context, result=None)
        return ParseResult.make_failure(context=context, expected=name, cause=r)

    return parse_lookahead


def lookahead[T](
    in_parser: Parser[T],
    /,
    *,
    name: str | None = None,
) -> Parser[None]:
    """Creates a parser that succeeds if the provided parser succeeds and reverse, without consuming any actual input

    Args:
        in_parser: The base parser
        name: Optionally, the name of the parser

    Returns:
        Composed parser
    """

    name = defaulted(name, f"lookahead({in_parser.name})")

    return _lookahead(in_parser, name=name)
