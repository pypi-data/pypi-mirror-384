from functools import cache

from .alternation import alternation
from .parse_result import ParseResult
from .parse_context import ParseContext
from .parser import Parser, parser
from pyforma._util import defaulted


@cache
def until(in_parser: Parser, /, *, name: str | None = None) -> Parser[str]:
    """Creates a parser consuming all input until the provided parser matches

    Args:
         in_parser: Parser matching the delimiter
         name: Optionally, the name of the parser

    Returns:
        A parser that matches any input until the provided parser matches. The delimiter is not consumed by this parser.
    """

    name = defaulted(name, f"until({in_parser.name})")

    @parser(name=name)
    def parse(context: ParseContext) -> ParseResult[str]:
        cur_context = context
        result = ""
        while not cur_context.at_eof():
            r = in_parser(cur_context)
            if r.is_success:
                break

            result += cur_context.peek()
            cur_context = cur_context.consume()

        return ParseResult.make_success(context=cur_context, result=result)

    return parse


@cache
def not_in(*parsers: Parser, name: str | None = None) -> Parser[str]:
    """Creates a parser consuming any input until one of the provided parsers matches

    Args:
        parsers: Parsers matching the delimiter
        name: The name of the parser

    Returns:
        A parser that matches any input until one of the provided parser matches. The delimiter is not consumed by this
        parser.
    """

    name = defaulted(name, f"not-in({', '.join(p.name for p in parsers)})")

    return until(alternation(*parsers), name=name)
