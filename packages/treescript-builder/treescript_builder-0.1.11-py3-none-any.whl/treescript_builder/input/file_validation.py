""" File Validation Methods.
 - These Methods all raise SystemExit exceptions.
 Author: DK96-OS 2024 - 2025
"""
from pathlib import Path
from stat import S_ISLNK
from sys import exit

from treescript_builder.input.string_validation import validate_name


_FILE_SIZE_LIMIT = 32 * 1024 # 32 KB
_FILE_SIZE_LIMIT_ERROR_MSG = "File larger than 32 KB Limit."
_FILE_SYMLINK_DISABLED_MSG = "Symlink file paths are disabled."

_FILE_DOES_NOT_EXIST_MSG = "The File does not Exist."
_FILE_READ_OSERROR_MSG = "Failed to Read from File."
_FILE_VALIDATION_ERROR_MSG = "Invalid Input File Contents."

_NOT_A_DIR_ERROR_MSG = "Not a Directory."
_DIR_DOES_NOT_EXIST_MSG = "The Directory does not exist."


def validate_input_file(file_name: str) -> str | None:
    """ Read the Input File, Validate (non-blank) data, and return Input str.
 - Max FileSize is 32 KB.
 - Symlink type file paths are disabled.

**Parameters:**
 - file_name (str): The Name of the Input File.

**Returns:**
 str - The String Contents of the Input File.

**Raises:**
 SystemExit - If the File does not exist, or is empty, blank, over 32 KB, or if the read or validation operation failed.
    """
    file_path = Path(file_name)
    try:
        if not file_path.exists():
            exit(_FILE_DOES_NOT_EXIST_MSG)
        if S_ISLNK((stat := file_path.lstat()).st_mode):
            exit(_FILE_SYMLINK_DISABLED_MSG)
        if stat.st_size > _FILE_SIZE_LIMIT:
            exit(_FILE_SIZE_LIMIT_ERROR_MSG)
        if (data := file_path.read_text()) is not None:
            if validate_name(data):
                return data
            exit(_FILE_VALIDATION_ERROR_MSG)
        # Fallthrough: return None
    except OSError:
        exit(_FILE_READ_OSERROR_MSG)
    return None


def validate_directory(dir_path_str: str | None) -> Path | None:
    """ Ensure that if the Directory argument is present, it Exists.
 - Allows None to pass through the method.

**Parameters:**
 - dir_path_str (str?): The String representation of the Path to the Directory.

**Returns:**
 Path? - The Path to the DataDirectory, or None if given input is None.

**Raises:**
 SystemExit - If a given path does not exist, or is not a Directory.
    """
    if dir_path_str is None:
        return None
    if (path := Path(dir_path_str)).exists():
        if path.is_dir():
            return path
        exit(_NOT_A_DIR_ERROR_MSG)
    exit(_DIR_DOES_NOT_EXIST_MSG)
