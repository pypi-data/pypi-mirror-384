from functools import cache

from .option import option
from .transform_result import transform_success
from .sequence import sequence
from .repetition import repetition
from .parser import Parser
from pyforma._util import defaulted


@cache
def _delimited[T, U](
    *, delim: Parser[T], content: Parser[U], allow_trailing_delim: bool, name: str
) -> Parser[tuple[U, ...]]:
    def _transform(
        success: None
        | tuple[U, tuple[tuple[T, U], ...]]
        | tuple[U, tuple[tuple[T, U], ...], T | None],
    ) -> tuple[U, ...]:
        if success is None:
            return ()
        return (success[0],) + tuple(e[1] for e in success[1])

    if allow_trailing_delim:
        return transform_success(
            option(
                sequence(content, repetition(sequence(delim, content)), option(delim)),
                name=name,
            ),
            transform=_transform,
        )
    return transform_success(
        option(
            sequence(content, repetition(sequence(delim, content))),
            name=name,
        ),
        transform=_transform,
    )


def delimited[T, U](
    *,
    delim: Parser[T],
    content: Parser[U],
    allow_trailing_delim: bool,
    name: str | None = None,
) -> Parser[tuple[U, ...]]:
    """Creates a parser for content delimited in between entries, and possibly at the end

    Args:
        delim: Parser for the delimiter
        content: Parser for the content
        allow_trailing_delim: Allow trailing delimiter at the end
        name: Optional parser name

    Returns:
        The composed parser. If no longer match is found, it returns an empty match.
    """

    name = defaulted(name, f"delimited({delim.name}, {content.name})")

    return _delimited(
        delim=delim,
        content=content,
        allow_trailing_delim=allow_trailing_delim,
        name=name,
    )
