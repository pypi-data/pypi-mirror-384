from collections.abc import Callable
from dataclasses import dataclass
from functools import lru_cache
from typing import overload, Any, Annotated, TypeVar, Generic

from annotated_types import MinLen

from .parse_result import ParseResult
from .parse_context import ParseContext

T = TypeVar("T", covariant=True, default=Any)


@dataclass(frozen=True)
class Parser(Generic[T]):
    """Concrete parser type"""

    parse: Callable[[ParseContext], ParseResult[T]]  # parser function
    name: Annotated[str, MinLen(1)]  # parser name

    def __call__(self, context: ParseContext) -> ParseResult[T]:
        """Parses the provided input using the parser function.

        Args:
            context: The parse context.

        Returns:
            The parsed result.
        """
        return self.parse(context)


type ParserDecorator[T = Any] = Callable[
    [Callable[[ParseContext], ParseResult[T]]], Parser[T]
]
"""Type of decorator for parser functions"""


@overload
def parser[T](
    function: Callable[[ParseContext], ParseResult[T]],
    /,
    *,
    name: str | None = None,
) -> Parser[T]:
    """Decorator that turns a function into a parser.

    Args:
        function: The function to be turned into a parser.
        name: Optional name for the parser. If None, the name is taken from the function name.

    Returns:
        The parser.

    Raises:
        TypeError: If name is None and the provided function has neither a __name__ nor a __class__.
    """


@overload
def parser[T](*, name: str) -> ParserDecorator[T]:
    """Factory for parser decorators generating parsers with a certain name.

    Args:
        name: Name of the parser

    Returns:
        A parser decorator that, when applied to a function, will turn it into a parser with the provided name.
    """


def parser[T](
    function: Callable[[ParseContext], ParseResult[T]] | None = None,
    /,
    *,
    name: str | None = None,
) -> Parser[T] | ParserDecorator[T]:
    """Parser decorator implementation"""

    if function is None:
        return lambda func, n=name: parser(func, name=n)

    if name is None:
        if hasattr(function, "__name__"):
            name = function.__name__
        elif hasattr(function, "__class__"):
            name = function.__class__.__name__
        else:  # Pathological case. Have to deliberately be un-pythonic to reach this.
            raise TypeError(f"Function {function} has no name")

    return Parser(lru_cache(function), name)
