"""The Arguments Received from the Command Line Input.
 - This DataClass is created after the argument syntax is validated.
 - Syntax Validation:
    - The Input File is Present and non-blank.
    - When Data Directory is present, it is non-blank.
 Author: DK96-OS 2024 - 2025
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class ArgumentData:
    """ The syntactically valid arguments received by the Program.

**Fields:**
 - input_file_path_str (str): The Name of the File containing the Tree Structure.
 - data_dir_path_str (str?): The Directory Name containing Files Used in File Tree Operation.
 - is_reversed (bool): Flag to determine if the File Tree Operation Is To be Oppositely Trimmed.
    """
    input_file_path_str: str
    data_dir_path_str: str | None
    is_reversed: bool