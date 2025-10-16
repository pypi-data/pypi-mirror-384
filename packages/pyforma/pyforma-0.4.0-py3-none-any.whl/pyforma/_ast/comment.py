from dataclasses import dataclass


@dataclass
class Comment:
    """Tagged string for comments."""

    text: str
