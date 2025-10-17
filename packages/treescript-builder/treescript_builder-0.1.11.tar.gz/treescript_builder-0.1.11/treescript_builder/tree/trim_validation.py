"""Tree Validation Methods for the Trim Operation.
 Author: DK96-OS 2024 - 2025
"""
from pathlib import Path
from typing import Generator, Callable

from treescript_builder.data.data_directory import DataDirectory, get_data_dir_validator
from treescript_builder.data.instruction_data import InstructionData
from treescript_builder.data.tree_data import TreeData
from treescript_builder.data.tree_state import TreeState


def validate_trim(
    tree_data: Generator[TreeData, None, None],
    data_dir_path: Path | None = None,
) -> tuple[InstructionData, ...]:
    """ Validate the Trim Instructions.

**Parameters:**
 - tree_data (Generator[TreeData]): The Generator that provides TreeData.
 - data_dir_path (Path?): The optional Path to a Data Directory. Default: None.

**Returns:**
 tuple[InstructionData] - A tuple of InstructionData.
    """
    return tuple(
        _validate_trim_generator(
            tree_data,
            get_data_dir_validator(
                data_dir=DataDirectory(data_dir_path) if data_dir_path is not None else None,
                is_trim=True,
            ),
        )
    )


def _validate_trim_generator(
    tree_data: Generator[TreeData, None, None],
    data_dir_validator: Callable[[TreeData], Path | None],
) -> Generator[InstructionData, None, None]:
    tree_state = TreeState()
    for node in tree_data:
        if tree_state.validate_tree_data(node) < 0:         # Calculate Tree Depth Change
            for i in tree_state.process_stack(node.depth):  # Pop Stack to required Depth
                yield InstructionData(True, i)
        if node.is_dir:
            tree_state.add_to_stack(node.name)              # Push Dir to Stack
        else:
            yield InstructionData(
                False,
                tree_state.get_current_path() / node.name,
                data_dir_validator(node)
            )
    for i in tree_state.process_stack(0):                   # Pop Remaining Stack Dirs
        yield InstructionData(True, i)
