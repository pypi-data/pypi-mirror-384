from functools import cache

from .parse_context import ParseContext
from .parse_result import ParseResult
from .parser import Parser, parser
from pyforma._util import defaulted


@cache
def _repetition[T](in_parser: Parser[T], /, *, name: str) -> Parser[tuple[T, ...]]:
    @parser(name=name)
    def parse_repetition(context: ParseContext) -> ParseResult[tuple[T, ...]]:
        cur_context = context
        results: list[T] = []
        while not cur_context.at_eof():
            r = in_parser(cur_context)
            if r.is_failure:
                break
            results.append(r.success.result)
            cur_context = r.context

        return ParseResult.make_success(context=cur_context, result=tuple(results))

    return parse_repetition


def repetition[T](
    in_parser: Parser[T],
    /,
    *,
    name: str | None = None,
) -> Parser[tuple[T, ...]]:
    """Creates a parser that repeatedly runs the provided parser

    Args:
        in_parser: The parser to run repeatedly
        name: Optionally, the parser name

    Returns:
        A parser repeatedly running the provided parser while it matches. If it never matches, an empty match is returned.
    """

    name = defaulted(name, f"repetition({in_parser.name})")

    return _repetition(in_parser, name=name)
