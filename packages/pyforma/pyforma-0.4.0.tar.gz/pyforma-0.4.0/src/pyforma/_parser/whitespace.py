from .munch import munch


whitespace = munch(str.isspace, name="whitespace")
"""Parses zero or more whitespace characters."""
