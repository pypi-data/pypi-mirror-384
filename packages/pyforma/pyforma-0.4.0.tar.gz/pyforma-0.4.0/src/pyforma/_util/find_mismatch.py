from collections.abc import Sequence


def find_mismatch[T](s1: Sequence[T], s2: Sequence[T]) -> int:
    """Reports the index of the first mismatching character, or -1 if no mismatch."""

    idx = next((i for i, (c1, c2) in enumerate(zip(s1, s2)) if c1 != c2), -1)

    if idx == -1 and len(s1) != len(s2):
        return min(len(s1), len(s2))
    else:
        return idx
