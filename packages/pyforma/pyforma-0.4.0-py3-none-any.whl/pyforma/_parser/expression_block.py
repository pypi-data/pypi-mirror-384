from functools import cache

from pyforma._parser.transform_result import transform_success

from .whitespace import whitespace
from .literal import literal
from .sequence import sequence
from .parser import Parser
from .expression import expression
from .template_syntax_config import BlockSyntaxConfig
from pyforma._ast.expression import Expression


@cache
def expression_block(syntax: BlockSyntaxConfig) -> Parser[Expression]:
    """Creates an expression block parser using the provided open and close markers

    Args:
        syntax: The syntax config to use

    Returns:
        The expression block parser.
    """

    return transform_success(
        sequence(
            literal(syntax.open),
            whitespace,
            expression,
            whitespace,
            literal(syntax.close),
            name="expression-block",
        ),
        transform=lambda result: result[2],
    )
