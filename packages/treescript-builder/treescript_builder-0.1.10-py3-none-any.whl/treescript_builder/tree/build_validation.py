""" Tree Validation Methods for the Build Operation.
 Author: DK96-OS 2024 - 2025
"""
from pathlib import Path
from typing import Generator

from treescript_builder.data.data_directory import DataDirectory
from treescript_builder.data.instruction_data import InstructionData
from treescript_builder.data.tree_data import TreeData
from treescript_builder.data.tree_state import TreeState


def validate_build(
    tree_data: Generator[TreeData, None, None],
    data_dir_path: Path | None = None,
) -> tuple[InstructionData, ...]:
    """ Validate the Build Instructions.

**Parameters:**
 - tree_data (Generator[TreeData]): The Generator that provides TreeData.
 - data_dir_path (Path?): The optional Data Directory Path. Default: None.

**Returns:**
 tuple[InstructionData] - A generator that yields Instructions.
    """
    return tuple(
        _validate_build_generator(tree_data)
        if data_dir_path is None else
        _validate_build_generator_data(tree_data, DataDirectory(data_dir_path))
    )


def _validate_build_generator(
    tree_data: Generator[TreeData, None, None]
) -> Generator[InstructionData, None, None]:
    tree_state = TreeState()
    for node in tree_data:
        # Error if any Nodes have Data Labels
        if node.data_label != '':
            exit(f"No DataDirectory provided, but DataLabel found on Line: {node.line_number}")
        # Calculate Tree Depth Change
        if tree_state.validate_tree_data(node) == 0:
            if node.is_dir:
                tree_state.add_to_queue(node.name)
            else:
                # Merge Queue into Stack
                if (new_dir := tree_state.process_queue()) is not None:
                    yield InstructionData(True, new_dir)
                yield InstructionData(
                    False, tree_state.get_current_path() / node.name
                )
        else:
            # Merge Queue into Stack
            if (new_dir := tree_state.process_queue()) is not None:
                yield InstructionData(True, new_dir, None)
            # Pop Stack to required Depth
            if not tree_state.reduce_depth(node.depth):
                exit(f"Invalid Depth at Line: {node.line_number}")
            if node.is_dir:
                tree_state.add_to_queue(node.name)
            else:
                yield InstructionData(
                    False, tree_state.get_current_path() / node.name
                )
    # Always Finish Build Sequence with ProcessQueue
    if (dir := tree_state.process_queue()) is not None:
        yield InstructionData(True, dir)


def _validate_build_generator_data(
    tree_data: Generator[TreeData, None, None],
    data_dir: DataDirectory
) -> Generator[InstructionData, None, None]:
    tree_state = TreeState()
    for node in tree_data:
        # Calculate Tree Depth Change
        if tree_state.validate_tree_data(node) == 0:
            if node.is_dir:
                tree_state.add_to_queue(node.name)
            else:
                # Build Queued Directories
                if (new_dir := tree_state.process_queue()) is not None:
                    yield InstructionData(True, new_dir)
                # Build File
                yield InstructionData(
                    False,
                    tree_state.get_current_path() / node.name,
                    data_dir.validate_build(node)
                )
        else:
            # Merge Queue into Stack
            if (new_dir := tree_state.process_queue()) is not None:
                yield InstructionData(True, new_dir)
            # Pop Stack to required Depth
            if not tree_state.reduce_depth(node.depth):
                exit(f"Invalid Tree Depth on Line {node.line_number} : {node.name}")
            if node.is_dir:
                tree_state.add_to_queue(node.name)
            else:
                yield InstructionData(
                    False,
                    tree_state.get_current_path() / node.name,
                    data_dir.validate_build(node)
                )
    # Always Finish Build Sequence with ProcessQueue
    if (dir := tree_state.process_queue()) is not None:
        yield InstructionData(True, dir)
