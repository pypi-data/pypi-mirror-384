from graphex_esxi_utils import exceptions
from time import time
from os import path, makedirs, remove
import esxi_utils
import re


def timeout(start_time: float, timeout_time: float) -> bool:
    """
    Returns True if the combined values are less than or equal to the current time
    (A timeout occured).
    :param start_time:
        The time the process started at
    :param timeout_time:
        The amout of time that is allowed to elapsed before triggering a timeout exception
    :return:
        True if the timeout has occured, False otherwise
    """
    return start_time + timeout_time <= time()


def extract_string_from_tag(all_text: str, tag_start: str, tag_end: str, start_index: int = 0):
    """
    Slices the given 'all_text' param based on the given start and end tags.
    :param all_text:
        the full block of text to slice
    :param tag_start:
        the starting tag (e.g. <serial>)
    :param tag_end:
        the ending tag (e.g. </serial>)
    :param start_index:
        where to start searching for the 'tag_start' parameter
    :return:
        the string extracted from all_text in-between the given tags
    """
    i = all_text.find(tag_start, start_index)
    if i < 0:
        raise exceptions.PaloAltoParsingError(f"ERROR: Unable to find start tag when extracting from string: {tag_start} ... start_index: {start_index}")
    i2 = all_text.find(tag_end, i)
    if i2 < 0:
        raise exceptions.PaloAltoParsingError(f"ERROR: Unable to find end tag when extracting from string: {tag_end}")
    return all_text[i + len(tag_start) : i2]


def convert_string_to_int(intstr: str, convert_forward: bool = True):
    """
    Attempts a straight conversion of the given string to an int. If a ValueError is thrown:
    will attempt to convert one character at a time and return the appended result.
    :param intstr:
        The string to be converted that supposably/usually contains an int
    :param convert_forward:
        When True: convert the characters in sequential order. When False: start from the back of the string AND only return the higher number of the string with characters.
        Example backwards: 11-h1 will return 1 whereas 11 will return 0 (there are no characters in 11 to break the conversion)
    :return:
        Either the full or partial integer from the specified direction.
    """
    try:
        convertion = int(intstr)
        if convert_forward:
            return convertion
        return 0
    except ValueError:
        temp = ""
        if convert_forward:
            for char in intstr:
                try:
                    int(char)
                    temp += char
                except ValueError:
                    break
        else:  # backward
            for i in range(len(intstr)):
                char = intstr[-i - 1]
                try:
                    int(char)
                    temp = char + temp
                except ValueError:
                    break
        try:
            return int(temp)
        except ValueError:
            raise exceptions.PaloAltoParsingError(f"ERROR: Unable to convert string to int! String: {intstr} .. Parsed: {temp}")


def create_abs_path(filepath: str) -> str:
    """
    Expands user variables (~) and then converts to an absolute path.
    :param filepath:
        the path to enforce as absolute
    :return:
        the expanded absolute filepath
    """
    return path.abspath(path.expanduser(filepath))


def remove_file(file_path: str):
    """
    Removes a file from the agent. Will not remove a directory.

    :param file_path:
        The file to remove
    """
    if path.exists(file_path):
        remove(file_path)


def create_dir_on_agent(dir_path: str):
    """
    Calls 'makedirs' on the agent to create the requested path.
    Will not error if the path already exists.
    May error if the provided path is invalid

    :param dir_path:
        The path to the directory to create.
    """
    makedirs(dir_path, exist_ok=True)


def get_response_debug_string(response: esxi_utils.util.Response) -> str:
    """
    Format a ``Response`` object into a printable debug string.

    :param response: The ``Response`` object.

    :return: The debug string.
    """
    debug_string = ""
    if "\n" in response.cmd:
        script_string = re.sub(r"^\s*", "  │  ", response.cmd, flags=re.MULTILINE)
        debug_string += f"Script:\n{script_string}"
    else:
        debug_string += f"Command: {response.cmd}"

    debug_string += f"\nStatus: {response.status}"

    if response.stdout.strip():
        indented_stdout = re.sub(r"^", "  │  ", str(response.stdout), flags=re.MULTILINE)
        debug_string += f"\nStdout:\n{indented_stdout}"

    if response.stderr.strip():
        indented_stderr = re.sub(r"^", "  │  ", str(response.stderr), flags=re.MULTILINE)
        debug_string += f"\nStderr:\n{indented_stderr}"

    debug_string = re.sub(r"^\s*", "  │  ", debug_string, flags=re.MULTILINE)
    return debug_string
