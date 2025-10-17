def bool_to_str(value: bool | None) -> str | None:
    """Convert a boolean value to a string representation."""
    if value is True:
        return "1"
    elif value is False:
        return "N"
    return None  # Return None for None
