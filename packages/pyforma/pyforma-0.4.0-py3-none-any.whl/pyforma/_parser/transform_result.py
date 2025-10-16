from collections.abc import Callable
from functools import cache

from .parse_result import ParseResult
from .parse_context import ParseContext
from .parser import Parser, parser
from pyforma._util import defaulted


@cache
def _transform_result[T, U](
    in_parser: Parser[T],
    /,
    *,
    transform: Callable[[ParseResult[T]], ParseResult[U]],
    name: str,
) -> Parser[U]:
    @parser(name=name)
    def parse_transform(context: ParseContext) -> ParseResult[U]:
        r = in_parser(context)
        return transform(r)

    return parse_transform


def transform_result[T, U](
    in_parser: Parser[T],
    /,
    *,
    transform: Callable[[ParseResult[T]], ParseResult[U]],
    name: str | None = None,
) -> Parser[U]:
    """Creates a parser that behaves like the provided parser but transforms the result

    Args:
        in_parser: The base parser
        transform: The transformation function
        name: Optional parser name

    Returns:
        Composed parser
    """

    name = defaulted(name, f"transform({in_parser.name}, {transform.__name__})")

    return _transform_result(in_parser, transform=transform, name=name)


def transform_success[T, U](
    in_parser: Parser[T],
    /,
    *,
    transform: Callable[[T], U],
    name: str | None = None,
) -> Parser[U]:
    """Creates a parser that behaves like the provided parser but transforms the result, if successful

        Args:
        in_parser: The base parser
        transform: The transformation function
        name: Optional parser name

    Returns:
        Composed parser
    """

    name = defaulted(name, f"transform_success({in_parser.name}, {transform.__name__})")

    def _transform(result: ParseResult[T]) -> ParseResult[U]:
        if result.is_success:
            return ParseResult.make_success(
                context=result.context, result=transform(result.success.result)
            )
        return ParseResult(result.failure, context=result.context)

    return _transform_result(in_parser, transform=_transform, name=name)


@cache
def _transform_consumed[T, U](
    in_parser: Parser[T],
    /,
    *,
    transform: Callable[[str], U],
    name: str,
) -> Parser[U]:
    @parser(name=name)
    def parse_transform(context: ParseContext) -> ParseResult[U]:
        r = in_parser(context)
        if r.is_success:
            consumed = context[: (r.context.index - context.index)]
            return ParseResult.make_success(
                context=r.context,
                result=transform(consumed),
            )
        return ParseResult(r.failure, context=r.context)

    return parse_transform


def transform_consumed[T, U](
    in_parser: Parser[T],
    /,
    *,
    transform: Callable[[str], U],
    name: str | None = None,
) -> Parser[U]:
    """Creates a parser that behaves like the provided parser but transforms the result, if successful

        Args:
        in_parser: The base parser
        transform: The transformation function
        name: Optional parser name

    Returns:
        Composed parser
    """

    name = defaulted(
        name,
        f"transform_consumed({in_parser.name}, {transform.__name__})",
    )

    return _transform_consumed(in_parser, transform=transform, name=name)
