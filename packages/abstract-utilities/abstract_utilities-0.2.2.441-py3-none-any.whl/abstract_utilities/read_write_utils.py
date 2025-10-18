"""
read_write_utils.py
-------------------
Unified read/write utility for safe file operations.
Supports:
- Writing content to a file
- Reading content from a file
- Creating and reading if missing
- Detecting file/content params via positional args or kwargs

Usage:
    from abstract_utilities.read_write_utils import *
"""

import os

_FILE_PATH_KEYS = ['file', 'filepath', 'file_path', 'path', 'directory', 'f', 'dst', 'dest']
_CONTENTS_KEYS = ['cont', 'content', 'contents', 'data', 'datas', 'dat', 'src', 'source']


# --- Helper utilities --------------------------------------------------------
def string_in_keys(strings, kwargs):
    """Find a matching keyword in kwargs that contains any of the given substrings."""
    for key in kwargs:
        for s in strings:
            if s.lower() in key.lower():
                return key
    return None


def get_path(paths):
    """Return the first valid path among given paths."""
    for path in paths:
        if isinstance(path, str):
            if os.path.isfile(path):
                return path
            dirname = os.path.dirname(path)
            if os.path.exists(dirname):
                return path
    return None


def break_down_find_existing(path):
    """Return the first non-existent subpath within a path chain."""
    test_path = ''
    for part in path.split(os.sep):
        test_path = os.path.join(test_path, part)
        if not os.path.exists(test_path):
            return test_path if test_path else None
    return test_path


# --- Parameter parsing --------------------------------------------------------
def check_read_write_params(*args, **kwargs):
    """
    Determine file_path and contents from arguments.
    Returns a tuple: (file_path, contents)
    """
    file_key = string_in_keys(_FILE_PATH_KEYS, kwargs)
    content_key = string_in_keys(_CONTENTS_KEYS, kwargs)

    file_path = kwargs.get(file_key) if file_key else None
    contents = kwargs.get(content_key) if content_key else None

    # Handle positional args (fallback)
    if file_path is None and len(args) > 0:
        file_path = args[0]
    if contents is None and len(args) > 1:
        contents = args[1]

    if file_path is None:
        raise ValueError("Missing file_path argument.")
    return file_path, contents


# --- Core functionality -------------------------------------------------------
def write_to_file(*args, **kwargs):
    """
    Write contents to a file (create if missing).

    Returns the file_path written.
    """
    file_path, contents = check_read_write_params(*args, **kwargs)
    if contents is None:
        raise ValueError("Missing contents to write.")

    os.makedirs(os.path.dirname(file_path) or ".", exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(str(contents))
    return file_path


def read_from_file(file_path):
    """Read text content from a file."""
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()


def create_and_read_file(*args, **kwargs):
    """
    Create the file (if missing) and read contents from it.
    """
    file_path, contents = check_read_write_params(*args, **kwargs)
    if not os.path.isfile(file_path):
        write_to_file(file_path, contents or "")
    return read_from_file(file_path)


def is_file_extension(obj: str) -> bool:
    """Return True if obj looks like a filename with extension."""
    if not isinstance(obj, str):
        return False
    root, ext = os.path.splitext(obj)
    return bool(root and ext)


def delete_file(file_path: str):
    """Safely delete a file if it exists."""
    if os.path.isfile(file_path):
        os.remove(file_path)
        return True
    return False


def get_content_lines(*args, **kwargs):
    """Return a list of lines from string or file path."""
    file_path, contents = check_read_write_params(*args, **kwargs)
    if os.path.isfile(file_path):
        contents = read_from_file(filepath)

    if isinstance(contents, str):
        return contents.splitlines()
    elif isinstance(contents, list):
        return contents
    return []
