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
        return all([result.scheme, result.netloc])
    except ValueError:
        return False
