import string

from .munch import munch


def _ishexdigit(s: str) -> bool:
    return all(c in string.hexdigits for c in s)


def _isoctdigit(s: str) -> bool:
    return all(c in string.octdigits for c in s)


def _isbindigit(s: str) -> bool:
    return all(c in ["0", "1"] for c in s)


digits = munch(str.isdigit, name="digits")
"""Parses zero or more digit characters."""

hexdigits = munch(_ishexdigit, name="hexdigits")
"""Parses zero or more hexadecimal digit characters."""

octdigits = munch(_isoctdigit, name="octdigits")
"""Parses zero or more octal digit characters."""

bindigits = munch(_isbindigit, name="bindigits")
"""Parses zero or more binary digit characters."""
