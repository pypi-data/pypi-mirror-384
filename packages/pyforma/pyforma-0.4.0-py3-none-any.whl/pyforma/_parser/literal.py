from functools import cache
from typing import LiteralString, overload

from pyforma._util.find_mismatch import find_mismatch

from .parse_context import ParseContext
from .parse_result import ParseResult
from .parser import Parser, parser


@overload
def literal[T: LiteralString](s: T, /) -> Parser[T]: ...


@overload
def literal(s: str, /) -> Parser[str]: ...


@cache
def literal(s: str, /) -> Parser[str]:
    """Creates a parser for a string literal.

    Args:
        s: The string literal.

    Returns:
        The parser for the given string.
    """

    name = f'"{s}"'

    @parser(name=name)
    def literal_parser(context: ParseContext) -> ParseResult[str]:
        if context[: len(s)] == s:
            return ParseResult.make_success(context=context.consume(len(s)), result=s)

        idx = find_mismatch(s, context[: len(s)])
        return ParseResult.make_failure(
            context=context,
            expected=name,
            cause=ParseResult.make_failure(
                context=context.consume(idx), expected=f'"{s[idx]}"'
            ),
        )

    return literal_parser
