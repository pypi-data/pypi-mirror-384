from urllib.parse import urlparse


def is_url(url: str):
    """
    Check if a given string is a valid URL.
    Code from https://stackoverflow.com/a/52455972

    Args:
        url (str): The string to be checked.

    Returns:
        bool: True if the string is a valid URL, False otherwise.
    """
    try:
        result = urlparse(url)
        # A valid URL must have a scheme
        if not result.scheme:
            return False

        # For most schemes, we need a netloc (network location)
        # But some schemes like 'file' and 'mailto' are valid without netloc
        if result.scheme in ["file", "mailto"]:
            return True

        # For other schemes, require netloc
        return bool(result.netloc)
    except ValueError:
        return False
