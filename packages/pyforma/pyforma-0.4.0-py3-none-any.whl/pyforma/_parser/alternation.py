from functools import cache
from typing import overload, NoReturn

from .parse_context import ParseContext
from .parse_result import ParseResult
from .parser import Parser, parser
from pyforma._util import defaulted


@overload
def alternation(*, name: str | None = None) -> NoReturn: ...


@overload
def alternation[T](
    p: Parser[T],
    /,
    *,
    name: str | None = None,
) -> Parser[T]: ...


@overload
def alternation[T1, T2](
    p1: Parser[T1],
    p2: Parser[T2],
    /,
    *,
    name: str | None = None,
) -> Parser[T1 | T2]: ...


@overload
def alternation[T1, T2, T3](
    p1: Parser[T1],
    p2: Parser[T2],
    p3: Parser[T3],
    /,
    *,
    name: str | None = None,
) -> Parser[T1 | T2 | T3]: ...


@overload
def alternation[T1, T2, T3, T4](
    p1: Parser[T1],
    p2: Parser[T2],
    p3: Parser[T3],
    p4: Parser[T4],
    /,
    *,
    name: str | None = None,
) -> Parser[T1 | T2 | T3 | T4]: ...


@overload
def alternation[T1, T2, T3, T4, T5](
    p1: Parser[T1],
    p2: Parser[T2],
    p3: Parser[T3],
    p4: Parser[T4],
    p5: Parser[T5],
    /,
    *,
    name: str | None = None,
) -> Parser[T1 | T2 | T3 | T4 | T5]: ...


@overload
def alternation[T1, T2, T3, T4, T5, T6](
    p1: Parser[T1],
    p2: Parser[T2],
    p3: Parser[T3],
    p4: Parser[T4],
    p5: Parser[T5],
    p6: Parser[T6],
    /,
    *,
    name: str | None = None,
) -> Parser[T1 | T2 | T3 | T4 | T5 | T6]: ...


@overload
def alternation[T1, T2, T3, T4, T5, T6, T7](
    p1: Parser[T1],
    p2: Parser[T2],
    p3: Parser[T3],
    p4: Parser[T4],
    p5: Parser[T5],
    p6: Parser[T6],
    p7: Parser[T7],
    /,
    *,
    name: str | None = None,
) -> Parser[T1 | T2 | T3 | T4 | T5 | T6 | T7]: ...


@overload
def alternation[T1, T2, T3, T4, T5, T6, T7, T8](
    p1: Parser[T1],
    p2: Parser[T2],
    p3: Parser[T3],
    p4: Parser[T4],
    p5: Parser[T5],
    p6: Parser[T6],
    p7: Parser[T7],
    p8: Parser[T8],
    /,
    *,
    name: str | None = None,
) -> Parser[T1 | T2 | T3 | T4 | T5 | T6 | T7 | T8]: ...


@overload
def alternation(*parsers: Parser, name: str | None = None) -> Parser: ...


def _farthest_parse(parse_result: ParseResult) -> int:
    while parse_result.is_failure and parse_result.failure.cause is not None:
        parse_result = parse_result.failure.cause

    return parse_result.context.index


@cache
def alternation(*parsers: Parser, name: str | None = None) -> Parser:
    """Create a parser that runs the provided parsers in sequence until one matches, then returns that result.

    Args:
        *parsers: Parsers to try one after another.
        name: Parser name.

    Returns:
        The alternation parser.
    """

    name = defaulted(name, f"alternation({', '.join(p.name for p in parsers)})")

    @parser(name=name)
    def parse_alternations(context: ParseContext) -> ParseResult:
        cause: ParseResult | None = None
        for p in parsers:
            result = p(context)
            if result.is_success:
                return result
            elif cause is None or (
                result.failure.cause
                and _farthest_parse(cause) < _farthest_parse(result)
            ):
                cause = result
        return ParseResult.make_failure(expected=name, context=context, cause=cause)

    return parse_alternations
