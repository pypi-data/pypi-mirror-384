from dataclasses import dataclass
from typing import Any, TypeVar, Generic, final, override

from .parse_context import ParseContext

T = TypeVar("T", covariant=True, default=Any)
U = TypeVar("U", contravariant=True, default=Any)


@dataclass(frozen=True)
class ParseSuccess(Generic[T]):
    result: T  # Parse result


@dataclass(frozen=True)
class ParseFailure:
    expected: str
    cause: "ParseResult | None" = None


@final
class ParseResult(Generic[T]):
    """Represents either a successful parse or a failed parse."""

    def __init__(
        self,
        value: ParseSuccess[T] | ParseFailure,
        /,
        *,
        context: ParseContext,
    ):
        self._value = value
        self._context = context

    @staticmethod
    def make_success(
        *,
        context: ParseContext,
        result: U,
    ) -> "ParseResult[U]":
        return ParseResult(ParseSuccess(result), context=context)

    @staticmethod
    def make_failure(
        *,
        context: ParseContext,
        expected: str,
        cause: "ParseResult|None" = None,
    ) -> "ParseResult[U]":
        return ParseResult(
            ParseFailure(expected=expected, cause=cause),
            context=context,
        )

    @property
    def context(self) -> ParseContext:
        return self._context

    @property
    def value(self) -> ParseSuccess[T] | ParseFailure:
        return self._value

    @property
    def success(self) -> ParseSuccess[T]:
        if isinstance(self._value, ParseSuccess):
            return self._value
        raise ValueError(f"{self.value} is not a successful parse")

    @property
    def failure(self) -> ParseFailure:
        if isinstance(self._value, ParseFailure):
            return self._value
        raise ValueError(f"{self.value} is not a failed parse")

    @property
    def is_success(self) -> bool:
        return isinstance(self._value, ParseSuccess)

    @property
    def is_failure(self) -> bool:
        return isinstance(self._value, ParseFailure)

    @override
    def __repr__(self) -> str:
        return f"ParseResult({repr(self.value)}, context={repr(self.context)})"

    @override
    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, ParseResult):
            return NotImplemented
        return self.value == other.value

    @override
    def __hash__(self) -> int:
        return hash(self.value)
