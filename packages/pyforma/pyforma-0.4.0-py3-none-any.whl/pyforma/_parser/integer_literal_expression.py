import ast

from .transform_result import transform_consumed
from .alternation import alternation
from .non_empty import non_empty
from .digits import bindigits, octdigits, hexdigits, digits
from .repetition import repetition
from .sequence import sequence
from .literal import literal
from pyforma._ast import ValueExpression

_bin_prefix = sequence(literal("0"), alternation(literal("b"), literal("B")))
_oct_prefix = sequence(literal("0"), alternation(literal("o"), literal("O")))
_hex_prefix = sequence(literal("0"), alternation(literal("x"), literal("X")))

_bin_int = sequence(
    _bin_prefix,
    non_empty(bindigits),
    repetition(sequence(literal("_"), non_empty(bindigits))),
)
_oct_int = sequence(
    _oct_prefix,
    non_empty(octdigits),
    repetition(sequence(literal("_"), non_empty(octdigits))),
)
_hex_int = sequence(
    _hex_prefix,
    non_empty(hexdigits),
    repetition(sequence(literal("_"), non_empty(hexdigits))),
)
_dec_int = sequence(
    non_empty(digits),
    repetition(sequence(literal("_"), non_empty(digits))),
)

integer_literal_expression = transform_consumed(
    alternation(
        _bin_int,
        _oct_int,
        _hex_int,
        _dec_int,
        name="integer literal",
    ),
    transform=lambda s: ValueExpression(ast.literal_eval(s)),
)
"""Parser for python-like integer literals"""
