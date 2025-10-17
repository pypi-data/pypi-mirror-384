import csv
import decimal
import re
from datetime import date, datetime
from io import StringIO
from pathlib import Path
from typing import Any, Iterable, List

import orjson
import toml

from .crypto import get_random_string
from .exceptions import FileOpenError, FileSaveError
from .logging import get_logger


def json_serializer(obj) -> str:
    """
    Serializes the given object to a JSON-compatible string representation.

    Args:
        obj: The object to be serialized.

    Returns:
        A JSON-compatible string representation of the object.

    Raises:
        TypeError: If the object is not JSON serializable.
    """

    if isinstance(obj, (datetime, date)):
        return obj.isoformat()

    if isinstance(obj, decimal.Decimal):
        return str(obj)

    raise TypeError("Type '{}' is not JSON serializable".format(type(obj)))


def read_file_json(json_file_path: Path) -> Any:
    """
    Accepts a Path object to a JSON file and reads it into a dict or array structure.

    Args:
        json_file_path (Path): The path to the JSON file.

    Returns:
        Union[dict, list]: The JSON data as a dictionary or list.

    Raises:
        FileNotFoundError: If the JSON file does not exist.
        FileOpenError: If there is an error while trying to read the file as JSON.
    """
    if not json_file_path.exists():
        raise FileNotFoundError(
            json_file_path,
            "File with path '{}' does not exist!".format(json_file_path.absolute()),
        )

    try:
        # Must include 'b' option for reading orjson
        file_bytes = __try_read_file(json_file_path, use_binary_read=True)
        return orjson.loads(file_bytes)
    except OSError as e:
        raise FileOpenError(
            json_file_path,
            "Error while trying to read file '{}' as JSON".format(json_file_path.absolute()),
        ) from e


def read_file_text(text_file_path: Path) -> str:
    """
    Accepts a path object to a file and reads it as text.

    Args:
        text_file_path (Path): The path to the text file.

    Returns:
        str: The contents of the file as a string.

    Raises:
        FileNotFoundError: If the file does not exist.
        FileOpenError: If there is an error while trying to read the file as text.
    """

    if not text_file_path.exists():
        raise FileNotFoundError(
            text_file_path,
            "File with path '{}' does not exist!".format(text_file_path.absolute()),
        )

    try:
        file_bytes = __try_read_file(text_file_path)
        return str(file_bytes)
    except OSError as e:
        raise FileOpenError(
            text_file_path,
            "Error while trying to read file '{}' as text".format(text_file_path.absolute()),
        ) from e


def read_file_toml(toml_file_path: Path) -> dict:
    """
    Accepts a path object to a file and reads it as a TOML configuration file

    Parameters:
        toml_file_path (Path): The path to the TOML file

    Returns:
        dict: The contents of the TOML file as a dictionary
    """

    file_contents = read_file_text(toml_file_path)
    return toml.loads(file_contents)


def read_file_csv(csv_file_path: Path, delimiter: str = ",", quote_char: str = '"') -> List:
    """
    Accepts a path object to a file and attempts to read it as a CSV file with optional
    delimiter and quote character specifications

    Args:
        csv_file_path (Path): The path to the CSV file.
        delimiter (str, optional): The delimiter used in the CSV file. Defaults to ",".
        quote_char (str, optional): The quote character used in the CSV file. Defaults to '"'.

    Returns:
        List: A list containing the rows of the CSV file.
    """

    file_contents = read_file_text(csv_file_path)
    csv_fp = StringIO(file_contents)
    csv_contents = []
    reader = csv.reader(csv_fp, delimiter=delimiter, quotechar=quote_char)
    for row in reader:
        csv_contents.append(row)

    return csv_contents


def __try_read_file(file_path: Path, use_binary_read=False) -> bytes:
    """
    Read file content into an array of bytes
    """

    file_mode = "r"
    if use_binary_read:
        file_mode += "b"

    with open(file_path.absolute(), file_mode) as f:
        return f.read()


def save_file_text(text_file_path: Path, data: Any, overwrite=False) -> None:
    """
    Accepts a Path object to a text file and writes the data to the file.

    Args:
        text_file_path (Path): The path to the text file.
        data (Any): The data to be written to the file.
        overwrite (bool, optional): Whether to overwrite the file if it already exists. Defaults to False.

    Raises:
        FileSaveError: If there is an error while trying to save the file.

    Returns:
        None
    """
    __check_save_file(text_file_path, overwrite)

    try:
        text_serialised_data = str(data)
        __try_save_file(text_file_path, text_serialised_data)
    except OSError as e:
        raise FileSaveError(
            text_file_path,
            "Error while trying to save file '{}' as text".format(text_file_path.absolute()),
        ) from e


def save_file_csv(
    csv_file_path: Path,
    data: Iterable[Iterable[Any]],
    delimiter: str = ",",
    quote_char: str = '"',
    escapechar: str | None = None,
    overwrite: bool = False,
) -> None:
    """
    Accepts a Path object to a csv text file and writes the data to the file

    :param csv_file_path: The path to the CSV file to be saved
    :type csv_file_path: Path
    :param data: The data to be written to the CSV file
    :type data: Iterable[Iterable[Any]]
    :param delimiter: The delimiter character used in the CSV file (default: ",")
    :type delimiter: str
    :param quote_char: The character used to quote fields in the CSV file (default: '"')
    :type quote_char: str
    :param escapechar: The character used to escape special characters in the CSV file (default: None)
    :type escapechar: Union[str, None]
    :param overwrite: Whether to overwrite the existing file if it already exists (default: False)
    :type overwrite: bool
    :return: None
    :raises FileSaveError: If there is an error while trying to save the file
    """

    __check_save_file(csv_file_path, overwrite)

    try:
        csv_fp = StringIO()
        csv.writer(csv_fp, delimiter=delimiter, quotechar=quote_char, escapechar=escapechar).writerows(data)

        __try_save_file(csv_file_path, csv_fp.getvalue())
    except OSError as e:
        raise FileSaveError(
            csv_file_path,
            "Error while trying to save file '{}' as CSV".format(csv_file_path.absolute()),
        ) from e


def save_file_json(json_file_path: Path, data: Any, overwrite=False) -> None:
    """
    Accepts a Path object to a JSON file and writes a dict to a JSON structure
    """
    default_serializer_options = (
        orjson.OPT_APPEND_NEWLINE
        | orjson.OPT_INDENT_2
        | orjson.OPT_NAIVE_UTC
        | orjson.OPT_SERIALIZE_NUMPY
        | orjson.OPT_SERIALIZE_UUID
        | orjson.OPT_OMIT_MICROSECONDS
        | orjson.OPT_STRICT_INTEGER
    )

    save_file_json_opts(json_file_path, data, overwrite, default_serializer_options)


def save_file_json_opts(
    json_file_path: Path,
    data: Any,
    overwrite: bool = False,
    serializer_opts: int | None = None,
) -> None:
    """
    Save data as a JSON file.

    Args:
        json_file_path (Path): The path to the JSON file.
        data (Any): The data to be saved as JSON.
        overwrite (bool, optional): Whether to overwrite the file if it already exists. Defaults to False.
        serializer_opts (dict, optional): Additional options for the JSON serializer. Defaults to None.
    """

    __check_save_file(json_file_path, overwrite)

    try:
        json_formatted_data = orjson.dumps(data, option=serializer_opts, default=json_serializer)

        # Must include 'b' option for writing orjson
        __try_save_file(json_file_path, json_formatted_data, use_binary_write=True)
    except OSError as e:
        raise FileSaveError(
            json_file_path,
            "Error while trying to save file '{}' as JSON".format(json_file_path.absolute()),
        ) from e


def __try_save_file(json_file_path: Path, data: Any, use_binary_write=False) -> None:
    """
    NOTE: Do not call this method directly. Use associated save_file_* functions
    """

    # Write the output to a random file and move into the correct location
    random_file_name = get_random_string()
    output_file_path = get_valid_file(json_file_path.parent, random_file_name)

    try:
        file_mode = "w"
        if use_binary_write:
            file_mode += "b"

        with open(output_file_path.absolute(), file_mode) as write_file:
            # If we are using a binary write mode and the data is not in the right
            # format (byte array), then convert it into a byte array before writing
            if use_binary_write and not isinstance(data, bytes):
                write_file.write(bytes(data, "utf8"))
            else:
                write_file.write(data)

        output_file_path.replace(json_file_path)
    except Exception:
        # Clean up our temporary file since there was an error in writing the output
        # We do not need to unlink on success because the file is replaced
        if output_file_path.exists():
            output_file_path.unlink()

        # Re-raise the exception
        raise


def __check_save_file(file_path: Path, overwrite: bool) -> bool:
    """
    Checks if a file can be overwritten based on the supplied path and overwrite flag
    """
    if file_path.exists() and not overwrite:
        raise FileSaveError(
            file_path,
            "File '{}' exists and the overwrite flag is not set to True!".format(file_path.absolute()),
        )

    return True


def get_valid_file(location_dir: Path, file_name: str, use_timestamp=False) -> Path:
    """
    Gets an output filename for a file in a path. If the file exists, it will
    append a "_x" where x is a number

    Optionally, add a timestamp to the file name instead of a sequential number
    """

    check_loop = 0
    while True:
        check_loop += 1
        if use_timestamp:
            file_name = append_value_to_filename(file_name, "_{}".format(int(datetime.now().timestamp())))

        candidate_file_name = Path(location_dir.absolute(), file_name)
        if not candidate_file_name.exists():
            break
        else:
            file_name = append_value_to_filename(file_name, "_{}".format(check_loop))

    return candidate_file_name


def append_value_to_filename(file_name: str, value_to_insert: str):
    """Inserts a value between the filename and the extension"""

    filename_parts = file_name.split(".")
    if len(filename_parts) <= 1:
        return "{}{}".format(file_name, value_to_insert)
    else:
        return "{}{}.{}".format(
            ".".join(filename_parts[0 : (len(filename_parts) - 1)]),
            value_to_insert,
            ".".join(filename_parts[len(filename_parts) - 1 : len(filename_parts)]),
        )


def get_timestamp_formatted_file_dir(
    parent_data_dir: Path, timestamp: datetime, resolution="HOUR", create_dir=False
) -> Path:
    """
    Creates and/or returns a formatted file directory based on the parent dir, the timestamp, and resolution
    """

    # Format numbers to have leading zeroes
    timestamp_blocks = (
        timestamp.strftime("%Y"),
        timestamp.strftime("%m"),
        timestamp.strftime("%d"),
        timestamp.strftime("%H"),
        timestamp.strftime("%M"),
        timestamp.strftime("%S"),
    )

    formatted_dir_prefix = ""

    # Notes:
    #
    # Reason for doing "YYYY-mm-dd" is that the total number of file system objects
    # will not exceed un-manageable levels (e.g. >10,000) in one directory.
    #
    # At the hour and minute level, every day is partitioned hourly, minute, and second dirs
    # as the number of file system objects can grow very large.
    #
    # If the number of file system objects is expected to be extremely large, use a hash-formatted
    # file directory structure, rather than this timestamp formatted file directory structure

    if resolution == "YEAR":
        formatted_dir_prefix = "/{}".format(*timestamp_blocks)
    elif resolution == "MONTH":
        formatted_dir_prefix = "/{}-{}".format(*timestamp_blocks)
    elif resolution == "DAY":
        formatted_dir_prefix = "/{}-{}-{}".format(*timestamp_blocks)
    elif resolution == "HOUR":
        formatted_dir_prefix = "/{}-{}-{}/{}".format(*timestamp_blocks)
    elif resolution == "MINUTE":
        formatted_dir_prefix = "/{}-{}-{}/{}/{}".format(*timestamp_blocks)
    else:
        formatted_dir_prefix = "/{}-{}-{}/{}/{}/{}".format(*timestamp_blocks)

    formatted_full_path = Path("{}/{}".format(parent_data_dir, formatted_dir_prefix))

    if create_dir and not formatted_full_path.exists():
        get_logger(__name__).debug(
            "Full path for this file does not exist. Creating '{}'".format(formatted_full_path.absolute())
        )
        formatted_full_path.mkdir(parents=True)

    return formatted_full_path


def get_cachekey(cache_ttl: int, timestamp: datetime | None = None) -> str:
    """
    Gets a cachekey tag (string) based on the current time and format
    """

    if timestamp is None:
        timestamp = datetime.now()

    cachekey_timestamp_format = get_timestamp_format_by_ttl_seconds(cache_ttl)

    return timestamp.strftime(cachekey_timestamp_format)


def get_timestamp_format_by_ttl_seconds(ttl_value: int) -> str:
    """
    Calculates the precision of the timestamp format required based on the TTL
    For example:
        if TTL is 3600 seconds (1hr) then return "%Y-%m-%d-%H0000"
        if TTL is 600 seconds (10 mins) then return "%Y-%m-%d-%H%M00"
        if TTL is 35 seconds (35 secs) then return "%Y-%m-%d-%H%M%S"
    """

    if ttl_value >= 86400:
        # Greater than one day, return a day timestamp
        return "%Y-%m-%d-000000"

    elif ttl_value >= 3600:
        # Greater than one hour, return an hour-based timestamp
        return "%Y-%m-%d-%H0000"

    elif ttl_value >= 60:
        # Greater than a minute, return a minute-based timestamp
        return "%Y-%m-%d-%H%M00"

    else:
        # Return a second-based timestamp
        return "%Y-%m-%d-%H%M%S"


def get_file_list_from_dir(parent_dir: Path, file_mask: str = "*") -> list:
    """
    Recursively gets a list of files in a Path directory with the specified name mask
    and return absolute string paths for files
    """
    get_logger(__name__).debug("Iterating for files in '{}'".format(parent_dir.absolute()))
    src_glob = parent_dir.rglob(file_mask)
    src_files = [str(f.absolute()) for f in src_glob if f.is_file()]
    get_logger(__name__).debug(
        "Iterated and found {} files in '{}'".format(len(src_files), parent_dir.absolute())
    )

    return src_files


def extract_timestamp_from_snapshot_key(snapshot_key: str) -> datetime:
    """
    Extracts the timespan from a snapshot key, such as from trending-snapshot-2021-01-01-143546
    """

    extraction_regex = r"(.*)([0-9]{4})-([0-9]{2})-([0-9]{2})-([0-9]{2})([0-9]{2})([0-9]{2})"
    matches = re.match(pattern=extraction_regex, string=snapshot_key)
    if matches is None:
        raise ValueError(f"Could not match the snapshot key with a valid regex: {snapshot_key}")

    (_, year, month, day, hour, minute, second) = matches.groups()

    return datetime(int(year), int(month), int(day), int(hour), int(minute), int(second), 0)


def prepare_timestamp_datapath(
    data_dir: Path,
    timestamp: datetime,
    data_dir_resolution: str = "DAY",
    data_file_timespan: int = 3600,
    data_file_prefix: str = "",
) -> Path:
    """
    Prepares a data path for data to be stored based on time frames, with an optional prefix

    Args:
        data_dir (Path): The base directory where the data will be stored.
        timestamp (datetime): The timestamp for which the data path is being prepared.
        data_dir_resolution (str, optional): The resolution of the data directory. Defaults to "DAY".
        data_file_timespan (int, optional): The timespan of the data file. Defaults to 3600.
        data_file_prefix (str, optional): The prefix to be added to the data file name. Defaults to "".

    Returns:
        Path: The prepared data path.

    """
    formatted_data_dir = get_timestamp_formatted_file_dir(data_dir, timestamp, data_dir_resolution)

    formatted_data_key = "{}{}".format(data_file_prefix, get_cachekey(data_file_timespan, timestamp))

    datapath_file = Path("{}/{}.json".format(formatted_data_dir, formatted_data_key))

    return datapath_file
