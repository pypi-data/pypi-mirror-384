import base64
import secrets
import string

ALPHA_CHARS = string.ascii_letters
NUM_CHARS = string.digits
ALPHA_NUM_CHARS = f"{ALPHA_CHARS}{NUM_CHARS}"

def get_random_number(min: int, max: int) -> int:
    """
    Gets a random number between min and max inclusive.

    Args:
        min (int): The minimum value of the random number (inclusive).
        max (int): The maximum value of the random number (inclusive).

    Returns:
        int: A random number between min and max (inclusive).
    """
    rand = secrets.SystemRandom()
    return rand.randint(min, max)


def get_random_string(
    length: int = 10, allowed_characters: str = ALPHA_NUM_CHARS
) -> str:
    """
    Gets a randomly generated alphanumeric string with the supplied length.

    Args:
        length (int, optional): The length of the generated string. Defaults to 10.
        allowed_characters (str, optional): The characters allowed in the generated string. Defaults to ALPHA_NUM_CHARS.

    Returns:
        str: A randomly generated alphanumeric string.
    """
    return "".join(secrets.choice(allowed_characters) for i in range(length))


def encode_base64(plain_string: str) -> str:
    """
    Encodes a URL-safe base64 version of a plain string.

    Args:
        plain_string (str): The plain string to be encoded.

    Returns:
        str: The URL-safe base64 encoded string.
    """
    return base64.urlsafe_b64encode(plain_string.encode("utf-8")).decode("utf-8")


def decode_base64(encoded_string: str) -> str:
    """
    Decodes a URL-safe base64 version of an encoded string.

    Args:
        encoded_string (str): The URL-safe base64 encoded string to be decoded.

    Returns:
        str: The decoded plain string.
    """
    return base64.urlsafe_b64decode(encoded_string).decode("utf-8")
