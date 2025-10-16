import ast
from pyforma._parser.transform_result import transform_consumed

from .alternation import alternation
from .option import option
from .non_empty import non_empty
from .digits import digits
from .repetition import repetition
from .sequence import sequence
from .literal import literal
from pyforma._ast import ValueExpression

_dec = sequence(
    non_empty(digits), repetition(sequence(literal("_"), non_empty(digits)))
)

floating_point_literal_expression = transform_consumed(
    sequence(
        _dec,
        alternation(
            sequence(
                literal("."),
                option(_dec),
            ),
            sequence(
                alternation(literal("e"), literal("E")),
                option(alternation(literal("-"), literal("+"))),
                _dec,
            ),
        ),
        name="float literal",
    ),
    transform=lambda s: ValueExpression(ast.literal_eval(s)),
)
