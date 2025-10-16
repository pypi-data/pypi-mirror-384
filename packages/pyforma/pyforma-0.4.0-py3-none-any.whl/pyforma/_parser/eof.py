from .parser import parser
from .parse_result import ParseResult
from .parse_context import ParseContext


@parser
def eof(context: ParseContext) -> ParseResult[None]:
    """Matches nothing at end of file"""
    if context.at_eof():
        return ParseResult.make_success(context=context, result=None)
    return ParseResult.make_failure(context=context, expected=eof.name)
