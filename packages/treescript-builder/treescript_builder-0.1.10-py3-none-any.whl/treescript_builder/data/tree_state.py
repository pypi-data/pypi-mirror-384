""" Tree State: A Key component in Tree Validation for Build operations.
 Author: DK96-OS 2024 - 2025
"""
from pathlib import Path
from sys import exit
from typing import Generator

from treescript_builder.data.path_stack import PathStack
from treescript_builder.data.tree_data import TreeData


class TreeState:
    """ Manages the State of the Tree during Validation.

**Method Summary:**
 - validate_tree_data(TreeData): int
 - get_current_depth: int
 - get_current_path: Path
 - add_to_queue(str)
 - add_to_stack(str)
 - process_queue: Path?
 - process_stack(int): Generator[Path]
 - reduce_depth(int): bool
    """

    def __init__(self):
        self._stack: PathStack = PathStack()
        self._queue: list = []
        self._prev_line_number: int = 0

    def validate_tree_data(self, node: TreeData) -> int:
        """ Ensure that the next TreeData is valid, relative to current state.
         - Calculate the change in depth, occurring with this TreeData.

        Parameters:
         - node (TreeData): The next TreeData in the sequence to Validate.

        Returns:
         int - The difference between the TreeData depth and the TreeState depth.

        Raises:
         SystemExit - When the TreeData is invalid, relative to the current TreeState.
        """
        self._update_line_number(node.line_number)
        # Calculate the Change in Depth
        if node.depth < 0:
            exit("Invalid Depth Value")
        # Ensure that the depth change is zero or less
        if (delta := node.depth - self.get_current_depth()) > 0:
            exit(f"You have jumped {delta} steps in the tree on line: {node.line_number}")
        return delta

    def get_current_depth(self) -> int:
        """ Determine the Current Depth of the Tree.
         - Includes Elements in both the Stack and the Queue.

        Returns:
         int - The total number of elements, combining stack and queue
        """
        return self._stack.get_depth() + len(self._queue)

    def get_current_path(self) -> Path:
        """ Obtain the Current Path of the Tree.

        Returns:
         str - A Path equivalent to the current Tree State.
        """
        if len(self._queue) > 0:
            self.process_queue()
        return self._stack.join_stack()

    def add_to_queue(self, dir_name: str):
        """ Add a directory to the Queue.

        Parameters:
         - dir_name (str): The name of the Directory to enqueue.
        """
        self._queue.append(dir_name)

    def add_to_stack(self, dir_name: str):
        """ Add a directory to the Stack.

        Parameters:
         - dir_name (str): The name of the Directory.
        """
        self._stack.push(dir_name)

    def process_queue(self) -> Path | None:
        """Process the Directories in the Queue.
         - Adds all directories from the Queue to the Stack.

        Returns:
         Path? - The whole Path from the Stack.
        """
        if len(self._queue) < 1:
            return None
        for element in self._queue:
            self._stack.push(element)
        self._queue.clear()
        # Return the new Path as a str
        return self._stack.join_stack()

    def process_stack(self, depth: int) -> Generator[Path, None, None]:
        """ Pop the Stack to the Desired Depth.
        - Combines all Elements in the Stack into a Directory Path.

        **Parameters:**
         - depth (int): The depth to process the stack to.

        **Yields:**
         Path - A Path for every Directory in the Stack, from top to bottom.
        """
        if depth < 0:
            raise ValueError('Negative Depth.')
        while depth < self._stack.get_depth():
            if (entry := self._stack.pop()) is not None:
                yield self._stack.join_stack() / entry

    def reduce_depth(self, depth: int) -> bool:
        """ Pop an element from the stack.

        Parameters:
         - depth (int): The Depth to pop the Stack to.

        Returns:
         bool - Whether the depth reduction succeeded, ie. 0 or more elements popped.
        """
        return self._stack.reduce_depth(depth)

    def _update_line_number(self, line_number: int):
        """ Validate the Line Number is always increasing.

        Parameters:
         - line_number (int): The line number from the next TreeData.

        Raises:
         SystemExit - When the Line Number does not increase.
        """
        if self._prev_line_number >= line_number:
            exit("Invalid Tree Data Sequence")
        self._prev_line_number = line_number
