from functools import cache

from .parse_context import ParseContext
from .parse_result import ParseResult
from .whitespace import whitespace
from .sequence import sequence
from .eof import eof
from .expression_block import expression_block
from .non_empty import non_empty
from .alternation import alternation
from .text import text
from .repetition import repetition
from .parser import Parser, parser
from .comment import comment
from .template_syntax_config import TemplateSyntaxConfig
from pyforma._ast.expression import Expression
from pyforma._ast.comment import Comment
from pyforma._ast.environment import Environment


@cache
def template(
    syntax: TemplateSyntaxConfig,
) -> Parser[tuple[str | Comment | Expression | Environment, ...]]:
    """Create a template parser

    Args:
        syntax: syntax config

    Returns:
        The template parser
    """

    @parser(name="template-bit")
    def _template_bit(
        context: ParseContext,
    ) -> ParseResult[str | Comment | Expression | Environment]:
        from .environment import environment

        _parse_text = non_empty(
            text(
                syntax.comment.open,
                syntax.expression.open,
                syntax.environment.open,
            )
        )

        return alternation(
            _parse_text,
            comment(syntax.comment),
            expression_block(syntax.expression),
            environment(syntax, _repeated_template_bit),
            name=_template_bit.name,
        )(context)

    @parser(name="repeated-template-bit")
    def _repeated_template_bit(
        context: ParseContext,
    ) -> ParseResult[tuple[str | Comment | Expression | Environment, ...]]:
        return repetition(_template_bit, name=_repeated_template_bit.name)(context)

    @parser(name="template")
    def _template(
        context: ParseContext,
    ) -> ParseResult[tuple[str | Comment | Expression | Environment, ...]]:
        result = _repeated_template_bit(context)

        if result.success and sequence(whitespace, eof)(result.context).is_success:
            return result
        t = whitespace(result.context)
        return ParseResult.make_failure(
            context=context,
            expected=_template.name,
            cause=_template_bit(t.context),
        )

    return _template
