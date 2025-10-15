""" Path Stack Management.
 Author: DK96-OS 2024 - 2025
"""
from pathlib import Path


class PathStack:
    """ A Stack of Directory names in a Path.

**Method Summary:**
 - push(str)
 - pop: str?
 - join_stack: Path
 - reduce_depth(int): bool
 - get_depth: int
    """

    def __init__(self):
        self._stack: list[str] = []

    def push(self, directory_name: str):
        """ Push a directory to the Path Stack.

**Parameters:**
 - directory_name (str): The name of the next directory in the Path Stack.
        """
        self._stack.append(directory_name)

    def pop(self) -> str | None:
        """ Pop the top of the Stack, and return the directory name.

**Returns:**
 str - The String removed from the top of the Stack.
        """
        if len(self._stack) <= 0:
            return None
        return self._stack.pop()

    def join_stack(self) -> Path:
        """ Combines all elements in the path Stack to form the parent directory.

**Returns:**
 Path - representing the current directory.
        """
        if len(self._stack) == 0:
            return Path("./")
        return Path(f"./{'/'.join(self._stack)}/")

    def reduce_depth(self, depth: int) -> bool:
        """ Reduce the Depth of the Path Stack.

**Parameters:**
 - depth (int): The depth to reduce the stack to.

**Returns:**
 boolean - Whether the Reduction was successful, ie 0 or more Stack pops.
        """
        if depth < 0 or (current_depth := self.get_depth()) < depth:
            return False
        if current_depth == depth:
            return True
        for _ in range(current_depth, depth, -1):
            self._stack.pop()
        return True

    def get_depth(self) -> int:
        """ Obtain the current Depth of the Stack.
 - The state where the current directory is the path, ie: './' has a depth of 0.

**Returns:**
 int - The number of elements in the Path Stack.
        """
        return len(self._stack)
