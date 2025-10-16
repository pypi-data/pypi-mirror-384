from functools import cache
from typing import Any, overload

from .parse_result import ParseResult
from .parse_context import ParseContext
from .parser import Parser, parser
from pyforma._util import defaulted


@overload
def sequence(
    *,
    name: str | None = None,
) -> Parser[tuple[()]]: ...


@overload
def sequence[T](
    p: Parser[T],
    /,
    *,
    name: str | None = None,
) -> Parser[tuple[T]]: ...


@overload
def sequence[T1, T2](
    p1: Parser[T1],
    p2: Parser[T2],
    /,
    *,
    name: str | None = None,
) -> Parser[tuple[T1, T2]]: ...


@overload
def sequence[T1, T2, T3](
    p1: Parser[T1],
    p2: Parser[T2],
    p3: Parser[T3],
    /,
    *,
    name: str | None = None,
) -> Parser[tuple[T1, T2, T3]]: ...


@overload
def sequence[T1, T2, T3, T4](
    p1: Parser[T1],
    p2: Parser[T2],
    p3: Parser[T3],
    p4: Parser[T4],
    /,
    *,
    name: str | None = None,
) -> Parser[tuple[T1, T2, T3, T4]]: ...


@overload
def sequence[T1, T2, T3, T4, T5](
    p1: Parser[T1],
    p2: Parser[T2],
    p3: Parser[T3],
    p4: Parser[T4],
    p5: Parser[T5],
    /,
    *,
    name: str | None = None,
) -> Parser[tuple[T1, T2, T3, T4, T5]]: ...


@overload
def sequence[T1, T2, T3, T4, T5, T6](
    p1: Parser[T1],
    p2: Parser[T2],
    p3: Parser[T3],
    p4: Parser[T4],
    p5: Parser[T5],
    p6: Parser[T6],
    /,
    *,
    name: str | None = None,
) -> Parser[tuple[T1, T2, T3, T4, T5, T6]]: ...


@overload
def sequence[T1, T2, T3, T4, T5, T6, T7](
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
) -> Parser[tuple[T1, T2, T3, T4, T5, T6, T7]]: ...


@overload
def sequence[T1, T2, T3, T4, T5, T6, T7, T8](
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
) -> Parser[tuple[T1, T2, T3, T4, T5, T6, T7, T8]]: ...


@overload
def sequence(
    *parsers: Parser[Any], name: str | None = None
) -> Parser[tuple[Any, ...]]: ...


@cache
def sequence(
    *in_parsers: Parser[Any],
    name: str | None = None,
) -> Parser[tuple[Any, ...]]:
    """Creates a parser that runs the provided parsers in sequence.

    Args:
        in_parsers: the parsers to run in sequence
        name: the name of the parser

    Returns:
        Parser that runs the provided parsers in sequence
    """

    name = defaulted(name, f"sequence({', '.join(p.name for p in in_parsers)})")

    @parser(name=name)
    def sequence_parser(context: ParseContext) -> ParseResult[tuple[Any, ...]]:
        cur_context = context
        results: list[Any] = []
        for p in in_parsers:
            r = p(cur_context)
            if r.is_failure:
                return ParseResult.make_failure(
                    context=context,
                    expected=name,
                    cause=r,
                )
            cur_context = r.context
            results.append(r.success.result)

        return ParseResult.make_success(context=cur_context, result=tuple(results))

    return sequence_parser
