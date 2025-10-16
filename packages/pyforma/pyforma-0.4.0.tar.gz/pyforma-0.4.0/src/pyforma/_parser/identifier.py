from .non_empty import non_empty
from .munch import munch


identifier = non_empty(munch(str.isidentifier), name="identifier")
"""Parses an identifier."""
