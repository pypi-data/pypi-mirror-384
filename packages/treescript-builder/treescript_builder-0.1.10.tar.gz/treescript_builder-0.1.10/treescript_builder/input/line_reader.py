""" Line Reader Module for Processing TreeScript.

The Default Input Reader.
 - Processes a single line at a time, and determines its key properties.
 - The Depth is the Integer number of directories between the current line and the root.
 - The Directory Boolean indicates whether the line represents a Directory.
 - The Name String is the name of the line.
 - DataLabel is the first word after the Name, and it has a strict set of validation criteria.
 - Comments are filtered out by starting a line with the # character. A comment after a file name is also filtered.
 Author: DK96-OS 2024 - 2025
"""
from sys import exit
from typing import Generator

from treescript_builder.data.tree_data import TreeData
from treescript_builder.input.string_validation import validate_dir_name, validate_name, validate_data_label


_INVALID_DEPTH_ERROR_MSG = "Invalid Depth (Number of Spaces) in Line: "

_INVALID_NODE_NAME_ERROR_MSG = "Invalid Name in Line: "
_INVALID_DATALABEL_ERROR_MSG = "Invalid DataLabel in Line: "
_MISSING_DATADIR_ERROR_MSG = "Missing DataDirectory for DataLabel in Line: "


def read_input_tree(
    input_tree_data: str,
) -> Generator[TreeData, None, None]:
    """ Generate structured Tree Data from the Input Data String.

**Parameters:**
 - input_data (InputData): The Input.

**Yields:**
 TreeData - Produces TreeData from the Input Data.

**Raises:**
 SystemExit - When any Line cannot be read successfully.
    """
    for line_number, line in enumerate(input_tree_data.splitlines(), start=1):
        if len(lstr := line.lstrip()) == 0 or lstr.startswith('#'):
            continue
        yield _process_line(line_number, line)


def _process_line(
    line_number: int,
    line: str,
) -> TreeData:
    """ Processes a single line of the input tree structure.
 - Returns a tuple indicating the depth, type (file or directory), name of file or dir, and file data if available.

**Parameters:**
 - line_number (int): The line-number in the input tree structure, starting from 1.
 - line (str): A line from the input tree structure.
 - is_data_label_enabled (bool): Whether DataLabels are enabled. If the DataDirectory argument is not provided, DataLabels are disabled.

**Returns:**
 TreeData - A Tree Node Data object.

**Raises:**
 SystemExit - When Line cannot be read successfully.
    """
    # Remove Leading Spaces (and trailing)
    if chr(32) in (args := line.strip()):
        args = args.split(chr(32))  # Split line into words.
        name = args[0]  # First Word is the Tree Node Name.
        # Second Word is the DataLabel.
        data_label = _validate_data_label_argument(line_number, args[1])
        # Additional Words are ignored. Comments after the DataLabel are possible, for now. 
        # Alternate LineReader Modules are likely to expand in this area:
    else:
        name, data_label = args, ''  # Was Not Split
    # Validate the Node Name and Type (is_dir). The tuple is bool first, then node name.
    if (node_info := _validate_node_name(name)) is None:
        exit(_INVALID_NODE_NAME_ERROR_MSG + str(line_number))
    return TreeData(
        line_number=line_number,
        depth=_calculate_depth(line_number, line),
        is_dir=node_info[0],
        name=node_info[1],
        data_label=data_label,
    )


def _validate_data_label_argument(
    line_number: int,
    argument: str,
) -> str:
    if argument.startswith('#'):  # Comment should be ignored.
        return ''
    elif not validate_data_label(argument):
        exit(_INVALID_DATALABEL_ERROR_MSG + str(line_number))
    return argument


def _validate_node_name(node_name: str) -> tuple[bool, str] | None:
    """ Determine whether this Tree Node is a Directory, and validate the name.

**Parameters:**
 - node_name (str): The argument received for the node name.

**Returns:**
 tuple[bool, str]? - Node information, first whether it is a directory, then the valid name of the node.
    
**Raises:**
 SystemExit - When the directory name is invalid.
    """
    try:
        # Check if the line contains any slash characters
        if (dir_name := validate_dir_name(node_name)) is not None:
            return True, dir_name
        # Fall-Through to File Node
    except ValueError:
        # An error in the dir name, such that it cannot be a file either
        return None
    # Is a File
    if validate_name(node_name):
        return False, node_name
    return None


def _calculate_depth(
    line_number: int,
    line: str
) -> int:
    """ Calculates the depth of a line in the tree structure.

**Parameters:**
 - line (str): A line from the tree command output.

**Returns:**
 int - The depth of the line in the tree structure, or -1 if space count is invalid.
    """
    space_count = len(line) - len(line.lstrip())
    # Bit Shift Shuffle Equivalence Validation (space_count is divisible by 2)
    if (depth := space_count >> 1) << 1 != space_count:
        # Invalid Space Count! Someone made an off-by-one whitespace mistake!
        exit(_INVALID_DEPTH_ERROR_MSG + str(line_number))
    return depth
