"""Helper functions for Klira AI SDK."""


def cameltosnake(camel_string: str) -> str:
    """
    Convert a camelCase string to snake_case.

    Helper function that's called recursively by camel_to_snake.

    Args:
        camel_string: String in camelCase format

    Returns:
        String in snake_case format
    """
    if not camel_string:
        return ""
    elif camel_string[0].isupper():
        return f"_{camel_string[0].lower()}{cameltosnake(camel_string[1:])}"
    else:
        return f"{camel_string[0]}{cameltosnake(camel_string[1:])}"


def camel_to_snake(s: str) -> str:
    """
    Convert a camelCase string to snake_case.

    Args:
        s: String in camelCase format

    Returns:
        String in snake_case format
    """
    if len(s) <= 1:
        return s.lower()

    return cameltosnake(s[0].lower() + s[1:])


def is_notebook() -> bool:
    """
    Check if code is running in a Jupyter notebook.

    Returns:
        bool: True if running in a Jupyter notebook, False otherwise
    """
    try:
        from IPython import get_ipython

        ip = get_ipython()
        if ip is None:
            return False
        return True
    except Exception:
        return False
