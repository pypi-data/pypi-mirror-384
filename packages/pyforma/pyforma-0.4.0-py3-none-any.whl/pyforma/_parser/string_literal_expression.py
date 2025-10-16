import ast

from .alternation import alternation
from .enclosed import enclosed
from .transform_result import transform_consumed
from .literal import literal
from .until import until
from pyforma._ast import ValueExpression


_string = alternation(
    enclosed(delim=literal('"'), content=until(literal('"'))),
    enclosed(delim=literal("'"), content=until(literal("'"))),
    name="string literal",
)


string_literal_expression = transform_consumed(
    _string,
    transform=lambda s: ValueExpression(ast.literal_eval(s)),
)
