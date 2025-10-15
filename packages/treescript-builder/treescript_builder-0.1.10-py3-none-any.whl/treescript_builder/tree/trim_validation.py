"""Tree Validation Methods for the Trim Operation.
 Author: DK96-OS 2024 - 2025
"""
from pathlib import Path
from typing import Generator

from treescript_builder.data.data_directory import DataDirectory
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
        _validate_trim_generator(tree_data)
        if data_dir_path is None else
        _validate_trim_generator_data(tree_data, DataDirectory(data_dir_path))
    )


def _validate_trim_generator(
    tree_data: Generator[TreeData, None, None]
) -> Generator[InstructionData, None, None]:
    tree_state = TreeState()
    for node in tree_data:
        # Error if any Nodes have Data Labels
        if node.data_label != '':
            exit(f"No DataDirectory provided, but DataLabel found on Line: {node.line_number}")
        # Calculate Tree Depth Change
        if tree_state.validate_tree_data(node) == 1:
            if node.is_dir:
                tree_state.add_to_stack(node.name)
            else:
                yield InstructionData(
                    False, tree_state.get_current_path() / node.name
                )
        else:
            # Pop Stack to required Depth
            for i in tree_state.process_stack(node.depth):
                yield InstructionData(True, i)
            if node.is_dir:
                tree_state.add_to_stack(node.name)
            else:
                yield InstructionData(
                    False, tree_state.get_current_path() / node.name
                )
    # Finish Trim Sequence with Pop Stack
    for i in tree_state.process_stack(0):
        yield InstructionData(True, i)


def _validate_trim_generator_data(
    tree_data: Generator[TreeData, None, None],
    data_dir: DataDirectory
) -> Generator[InstructionData, None, None]:
    tree_state = TreeState()
    for node in tree_data:
        # Calculate Tree Depth Change
        if tree_state.validate_tree_data(node) == 1:
            if node.is_dir:
                tree_state.add_to_stack(node.name)
            else:
                yield InstructionData(
                    False,
                    tree_state.get_current_path() / node.name,
                    data_dir.validate_trim(node)
                )
        else:
            # Pop Stack to required Depth
            for i in tree_state.process_stack(node.depth):
                yield InstructionData(True, i)
            if node.is_dir:
                tree_state.add_to_stack(node.name)
            else:
                yield InstructionData(
                    False,
                    tree_state.get_current_path() / node.name,
                    data_dir.validate_trim(node)
                )
    # Finish Trim Sequence with Pop Stack
    for i in tree_state.process_stack(0):
        yield InstructionData(True, i)
