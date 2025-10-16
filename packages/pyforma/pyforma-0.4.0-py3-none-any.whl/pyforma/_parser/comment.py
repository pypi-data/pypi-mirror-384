from functools import cache

from .template_syntax_config import BlockSyntaxConfig
from .parser import parser, Parser
from .parse_context import ParseContext
from .parse_result import ParseResult
from pyforma._ast import Comment
from pyforma._util import defaulted


@cache
def comment(
    syntax: BlockSyntaxConfig,
    /,
    *,
    name: str | None = None,
) -> Parser[Comment]:
    """Creates a comment parser using the provided open and close markers

    Args:
        syntax: Syntax config to use
        name: Optional parser name

    Returns:
        The comment parser.
    """

    name = defaulted(name, f'comment("{syntax.open}", "{syntax.close}")')

    @parser(name=name)
    def parse_comment(context: ParseContext) -> ParseResult[Comment]:
        cur_context = context

        if not cur_context[:].startswith(syntax.open):
            return ParseResult.make_failure(
                expected=f'"{syntax.open}"',
                context=context,
            )

        cur_context = cur_context.consume(len(syntax.open))

        result = ""
        while not cur_context.at_eof():
            if cur_context[:].startswith(syntax.open):
                r = parse_comment(cur_context)
                result += f"{syntax.open}{r.success.result.text}{syntax.close}"
                cur_context = r.context
            elif cur_context[:].startswith(syntax.close):
                return ParseResult.make_success(
                    context=cur_context.consume(len(syntax.close)),
                    result=Comment(result),
                )
            else:
                result += cur_context.peek()
                cur_context = cur_context.consume()

        return ParseResult.make_failure(
            context=context,
            expected=name,
            cause=ParseResult.make_failure(
                expected=f'"{syntax.close}"', context=cur_context
            ),
        )

    return parse_comment
