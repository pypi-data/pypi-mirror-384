def defaulted[T, U](value: T | None, default: U) -> T | U:
    """Returns value as-is, except when it's None."""
    if value is None:
        return default
    return value
