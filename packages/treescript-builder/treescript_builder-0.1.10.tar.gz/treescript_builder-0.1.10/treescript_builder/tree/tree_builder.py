"""Tree Building Operations.
 Author: DK96-OS 2024 - 2025
"""
from pathlib import Path
from shutil import copy2

from treescript_builder.data.instruction_data import InstructionData


def build(instructions: tuple[InstructionData, ...]) -> tuple[bool, ...]:
    """ Execute the Instructions in build mode.

**Parameters:**
 - instructions(tuple[InstructionData]): The Instructions to execute.

**Returns:**
 tuple[bool] - The success or failure of each instruction.
    """
    return tuple(_build(i) for i in instructions)


def _build(i: InstructionData) -> bool:
    """ Execute a single instruction.

**Parameters:**
 - instruction(InstructionData): The data required to execute the operation.

**Returns:**
 bool - Whether the given operation succeeded.
    """
    if i.is_dir:
        return _make_dir_exist(i.path)
    elif i.data_path is None:
        i.path.touch(exist_ok=True)
        return True
    else:
        return _create_file(i.path, i.data_path)


def _create_file(
    path: Path,
    data: Path
) -> bool:
    """ Create a File at the given path, with data from the Data Directory.

**Parameters:**
 - path (Path): The Path to the File to be created, and written to.
 - data (Path): A Data Directory Path to be copied to the new File.

**Returns:**
 bool - Whether the File operation succeeded.
    """
    try:
        copy2(data, path)
    except OSError:
        return False
    return True


def _make_dir_exist(
    path: Path
) -> bool:
    """ Ensure that the Directory at the given Path exists.

**Parameters:**
 - path (Path): The Path to the File to be created, and written to.

**Returns:**
 bool - True if the Operation Succeeded, or if the Path already exists.
    """
    if path.exists():
        return True
    try:
        path.mkdir(parents=True, exist_ok=True)
    except OSError:
        return False
    return True