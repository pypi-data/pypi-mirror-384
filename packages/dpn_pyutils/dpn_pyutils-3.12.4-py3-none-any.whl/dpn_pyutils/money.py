def format_currency_market_display_float(value: float, currency_symbol: str = "$", suffix: str = "") -> str:
    """
    Formats a currency value according to conventional market display conventions
    using floating-point numbers.

    IMPORTANT: This function uses floats for display purposes only. For financial
    calculations involving large amounts or high decimal precision, use decimal
    types or integer arithmetic to avoid floating-point precision errors.

    Formatting Conventions:
        Values less than 0.000001:
            - Display with "<" prefix for positive values
            - Show leading minus sign for negative values
            - Include currency symbol and literal "0.000001"
            - Examples: <$0.000001 or <-$0.000001

        Values between 0.000001 and 0.01:
            - Show leading minus sign for negative values
            - Include currency symbol with 6 decimal places
            - Handles precision display for small fractional amounts
            - Examples: $0.002895 or -$0.000690

        Values between 0.01 and 0.99:
            - Show leading minus sign for negative values
            - Include currency symbol with 2 decimal places
            - Standard currency formatting for fractional amounts
            - Examples: $0.25 or -$0.50

        Values between $1.00 and $999.99:
            - Standard currency formatting with 2 decimal places
            - No special prefixes or suffixes applied
            - Examples: $123.45 or $1.00

        Values between $1,000 and $999,999:
            - Show leading minus sign for negative values
            - Include currency symbol with 2 decimal places
            - Add 'K' suffix to indicate thousands
            - Examples: $15.23K or -$250.00K

        Values between $1,000,000 and $999,999,999:
            - Show leading minus sign for negative values
            - Include currency symbol with 1 decimal place
            - Add 'M' suffix to indicate millions
            - Examples: $2.5M or -$100.0M

        Values of $1,000,000,000 and above:
            - Show leading minus sign for negative values
            - Include currency symbol with 1 decimal place
            - Add 'B' suffix to indicate billions
            - Examples: $1.2B or -$5.5B

        Values of $1,000,000,000,000 and above:
            - Show leading minus sign for negative values
            - Include currency symbol with 1 decimal place
            - Add 'T' suffix to indicate trillions
            - Examples: $2.1T or -$10.5T

    Args:
        value: The numeric value to format as currency
        currency_symbol: The currency symbol to use (default: "$")
        suffix: Additional suffix to append after the formatted value

    Returns:
        A formatted string representing the currency value according to
        market display conventions
    """

    value_opts = {
        "negative_qty": False if value >= 0 else True,
        "prefix": "",
        "currency_symbol": currency_symbol,
        "value": "",
        "summary_suffix": "",
        "suffix": suffix,
    }

    # Format Trillions
    if abs(value) >= float(1e12):
        chopped_value = value / 1e12
        value_opts["value"] = "{:.1f}".format(abs(chopped_value))
        value_opts["summary_suffix"] = "T"

    # Format Billions
    elif abs(value) >= float(1e9):
        chopped_value = value / 1e9
        value_opts["value"] = "{:.1f}".format(abs(chopped_value))
        value_opts["summary_suffix"] = "B"

    # Format Millions
    elif abs(value) >= float(1e6):
        chopped_value = value / float(1e6)
        value_opts["value"] = "{:.1f}".format(abs(chopped_value))
        value_opts["summary_suffix"] = "M"

    # Format Thousands
    elif abs(value) >= float(1e3):
        chopped_value = value / float(1e3)
        value_opts["value"] = "{:.2f}".format(abs(chopped_value))
        value_opts["summary_suffix"] = "k"

    # Format Fractional
    elif abs(value) > 0 and abs(value) < 1:
        # If the fractional value is greater than 0.01
        if abs(value) > float(1e-2):
            value_opts["value"] = "{:.2f}".format(abs(value))

        # If the fractional value is greater than 6 decimal places (i.e. >=0.000001)
        elif abs(value) > float(1e-6):
            # Due to python's formatting of values with lots of leading zeroes into scientific
            # notation, we need to we need to truncate
            value_opts["value"] = "{:.17f}".format(float("{:.6f}".format(abs(value)))).rstrip("0")

        # If the fractional value is less than 6 decimal places (i.e. <0.000001)
        else:
            value_opts["prefix"] = "<"
            value_opts["value"] = "0.000001"

    # Format small numbers
    else:
        value_opts["value"] = "{:.2f}".format(abs(value))

    # Generate our formatted value
    formatted_value = "{}{}{}{}{}{}".format(
        value_opts["prefix"],
        "-" if value_opts["negative_qty"] else "",
        value_opts["currency_symbol"],
        value_opts["value"],
        value_opts["summary_suffix"],
        value_opts["suffix"],
    )

    return formatted_value
