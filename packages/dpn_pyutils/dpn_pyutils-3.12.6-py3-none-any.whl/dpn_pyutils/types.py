"""
This module provides stateless utility functions for type checking and conversion.

This module contains functions that help with:
- Identifying and validating numeric types (integers, floats)
- Checking boolean representations in strings
- Parsing string inputs into appropriate Python types

All functions are stateless and can be used for input validation and type conversion.
"""

TRUE_BOOLS = [
    "true",
    "yes",
    "1",
]

FALSE_BOOLS = [
    "false",
    "no",
    "0",
]


def is_numeric(n: str) -> bool:
    """
    Check if a string represents a valid numeric value.

    This function attempts to convert the input string to a float and returns True
    if successful, indicating the string contains a valid numeric representation.
    It handles both integer and floating-point representations.

    Args:
        n (str): The string to check for numeric content

    Returns:
        bool: True if the string can be converted to a number, False otherwise

    Examples:
        >>> is_numeric("123")
        True
        >>> is_numeric("123.45")
        True
        >>> is_numeric("abc")
        False
        >>> is_numeric("")
        False

    Note:
        This function considers any string that can be parsed as a float as numeric,
        including exponential notation (e.g., "1.23e10").
    """

    try:
        return True if float(n) else float(n).is_integer()
    except ValueError:
        return False
    except TypeError:
        return False


def is_integer(n: str) -> bool:
    """
    Check if a string represents a valid integer value.

    This function attempts to convert the input string to a float first, then checks
    if the resulting number is a whole number (i.e., has no decimal component).
    This means it will return True for strings like "123" and "123.0" but False
    for "123.45".

    Args:
        n (str): The string to check for integer content

    Returns:
        bool: True if the string represents an integer value, False otherwise

    Examples:
        >>> is_integer("123")
        True
        >>> is_integer("123.0")
        True
        >>> is_integer("123.45")
        False
        >>> is_integer("abc")
        False
        >>> is_integer("1.23e2")  # 123.0
        True

    Note:
        This function considers strings in exponential notation that result in
        whole numbers as integers (e.g., "1e2" = 100, "2e0" = 2).
    """
    try:
        float(n)
    except (ValueError, TypeError):
        return False
    else:
        return float(n).is_integer()


def is_boolean(n: str) -> bool:
    """
    Check if a string represents a valid boolean value.

    This function checks if the input string matches any of the predefined boolean
    representations, case-insensitively. The recognized boolean values are:
    - True: "true", "yes", "1"
    - False: "false", "no", "0"

    Args:
        n (str): The string to check for boolean content

    Returns:
        bool: True if the string represents a boolean value, False otherwise

    Examples:
        >>> is_boolean("true")
        True
        >>> is_boolean("YES")
        True
        >>> is_boolean("false")
        True
        >>> is_boolean("No")
        True
        >>> is_boolean("maybe")
        False
        >>> is_boolean("2")
        False

    Note:
        The check is case-insensitive, so "TRUE", "True", and "true" all return True.
        Only the specific values listed above are considered valid boolean representations.
    """

    try:
        if n.lower() in TRUE_BOOLS or n.lower() in FALSE_BOOLS:
            return True
    except (ValueError, AttributeError):
        return False
    else:
        return False


def parse_type(n: str) -> str | int | float | bool | None:
    """
    Parse a string input and convert it to the appropriate Python type.

    This function attempts to intelligently parse a string input and return it as
    the most appropriate Python type. The parsing follows this priority order:
    1. If numeric and integer → return int
    2. If numeric but not integer → return float
    3. If boolean → return bool
    4. If empty string → return None
    5. Otherwise → return original string

    Args:
        n (str): The string to parse and convert

    Returns:
        str | int | float | bool | None: The parsed value in the appropriate type:
            - int: If the string represents a whole number
            - float: If the string represents a decimal number
            - bool: If the string represents a boolean value
            - None: If the string is empty
            - str: If the string doesn't match any of the above patterns

    Examples:
        >>> parse_type("123")
        123
        >>> parse_type("123.45")
        123.45
        >>> parse_type("true")
        True
        >>> parse_type("false")
        False
        >>> parse_type("")
        None
        >>> parse_type("hello")
        'hello'
        >>> parse_type("1e2")  # 100
        100

    Note:
        Boolean parsing is case-insensitive and recognizes: "true", "yes", "1" as True;
        "false", "no", "0" as False. Empty strings return None rather than False.
    """

    if is_numeric(n):
        if is_integer(n):
            return int(float(n))
        else:
            return float(n)
    else:
        if is_boolean(n):
            if n.lower() in TRUE_BOOLS:
                return True
            elif n.lower() in FALSE_BOOLS:
                return False
        elif n == "":
            return None

        return n
