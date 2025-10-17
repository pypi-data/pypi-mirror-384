from colorama import Back, Fore, Style
from colorama.ansi import AnsiCodes


def color_t(text: str, color: AnsiCodes | str) -> str:
    """
    Returns a colour formatted text with default background
    """
    return color_format_string(text, color, Back.RESET)


def color_var_fore(label: str, value: str, color: AnsiCodes | str) -> str:
    """
    Returns a colour formatted string of a variable or key-value pair with a white label and coloured value
    """
    return color_var(label, Fore.RESET, value, color)


def color_var(
    label: str,
    label_color: AnsiCodes | str,
    value: str,
    value_color: AnsiCodes | str,
) -> str:
    """
    Returns a colour formatted string of a variable or key-value pair
    """
    return color_var_fore_back(
        label, label_color, Back.RESET, value, value_color, Back.RESET
    )


def color_var_fore_back(
    label: str,
    label_color_fore: AnsiCodes | str,
    label_color_back: AnsiCodes | str,
    value: str,
    value_color_fore: AnsiCodes | str,
    value_color_back: AnsiCodes | str,
):
    """
    Returns a colour formatted string that represents a variable or key-value pair
    """

    formatted_string = "{} {}".format(
        # Format label (or key)
        color_format_string(label, label_color_fore, label_color_back),
        # Format value
        color_format_string(value, value_color_fore, value_color_back),
    )

    return formatted_string


def color_format_string(
    text: str, color_fore: AnsiCodes | str, color_back: AnsiCodes | str
) -> str:
    """
    Format text with foreground, background and reset
    """

    return "{}{}{}{}".format(color_fore, color_back, text, Style.RESET_ALL)
