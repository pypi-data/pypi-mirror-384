""" String Validation Methods.
 Author: DK96-OS 2024 - 2025
"""
from itertools import permutations, repeat
from typing import Literal


def validate_name(argument) -> bool:
    """ Determine whether an argument is a non-empty string.
 - Does not count whitespace.
 - Uses the strip method to remove empty space.

**Parameters:**
 - argument (str): The given argument, which needs validation.

**Returns:**
 bool - True if the argument qualifies as valid.
    """
    if argument is None or not isinstance(argument, str):
        return False
    elif len(argument.strip()) < 1:
        return False
    return True


def validate_data_label(data_label: str) -> bool:
    """ Determine whether a Data Label is Valid.
 - Allows the approved non-alphanumeric chars.
 - The exclamation point (!) is a valid DataLabel, if by itself.
 - If a slash char is found in the string, it is invalid.
 - Small strings (length <= 2) consisting of only punctuation are invalid.

**Parameters:**
 - data_label (str): The String to check for validity.

**Returns:**
 bool - Whether the String is a valid Data Label.
    """
    if len(data_label) < 3:
        if '!' == data_label: # 33
            return True
        if data_label == '' or _is_invalid_small_tree_string(data_label):
            return False
    elif len(data_label) > 99:
        return False
    for ch in data_label:
        n = ord(ch)
        # ALLOWED: Special Punctuation (-._) Codes: 45, 46, 95
        # Numbers: 48 - 57
        # UpperCase: 65 - 90
        # LowerCase: 97 - 122
        if not (n != 47 and 45 <= n <= 57 if n < 65 else n <= 90 or n <= 122 and (n == 95 or 97 <= n)):
            return False
    return True


def validate_dir_name(dir_name: str) -> str | None:
    """ Determine that a directory is correctly formatted.

**Parameters:**
 - dir_name (str): The given input to be validated.

**Returns:**
 str? - The valid directory name, or none if it may be a file.

**Raises:**
 ValueError - When the name is not suitable for directories or files.
    """
    if (name_length := len(dir_name)) >= 100: # Keep Name Length Reasonable
        raise ValueError(f'Name too Long!: {name_length}')
    # Check for slash chars
    if (name := _filter_slash_chars(dir_name)) is not None: # Is a Dir
        # Validate chars (parent dir, current dir)
        if name in ['', '.', '..']:
            raise ValueError('Invalid Directory')
        return name
    else: # Is a File
        return None


def _is_invalid_small_tree_string(tree_string: str) -> bool:
    """ Checks strings of length 1 or 2 for invalid combinations of chars that are generally valid in larger strings..
 - The dot strings are not allowed because they may escape the DataDirectory.
 - The permutations including line characters are not allowed, to help prevent mistakes (typos) and so on.
 
**Parameters:**
 - data_label (str): The Data Label to check, which should be of length 2 or 1.

**Returns:**
 bool - True, if the given parameter is invalid, given the specific filtering criteria.
    """
    return tree_string in (invalid_chars := ('.', '_', '-')) or \
        tree_string in (''.join(repeat(x, 2)) for x in invalid_chars) or \
        tree_string in permutations(invalid_chars, 2)


def _validate_slash_char(dir_name: str) -> Literal['\\', '/'] | None:
    """ Determine which slash char is used by the directory, if it is a directory.
 - Discourages use of both slash chars, by raising ValueError.

**Parameters:**
 - dir_name (str): The given input to be validated.

**Returns:**
 str? - The slash character used, or none if no chars were found.

**Raises:**
 ValueError - When the name contains both slash characters.
    """
    slash: Literal['\\', '/'] | None = None
    if '/' in dir_name:
        slash = '/'
        # Also check for other slash
    if '\\' in dir_name:
        if slash is not None:
            raise ValueError('Invalid character combination: forward and back slash in the same path.')
        slash = '\\'
    return slash


def _filter_slash_chars(dir_name: str) -> str | None:
    """ Remove all of the slash characters and return the directory name.
 - Returns None when there are no slash characters found.

**Parameters:**
 - dir_name (str): The given input to be validated.

**Returns:**
 str? - The valid directory Name, or None if it may be a file (there were no slash chars found).

**Raises:**
 ValueError - When the name is not suitable for directories or files, such as when slash characters are used improperly.
    """
    slash: Literal['\\', '/'] | None = _validate_slash_char(dir_name)
    if slash is None: # No slash chars found.
        return None
    if dir_name.endswith(slash) or dir_name.startswith(slash):
        name: str = dir_name.strip(slash)
        if slash in name: # Has internal slash characters
            raise ValueError('Multi-dir line detected')
    else:
        # Found slash chars only within the node name (multi-dir line)
        raise ValueError('Multi-dir line detected')
    return name
