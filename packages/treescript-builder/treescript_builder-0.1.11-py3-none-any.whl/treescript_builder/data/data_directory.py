""" Data Directory Management.
 Author: DK96-OS 2024 - 2025
"""
from pathlib import Path
from sys import exit
from typing import Callable

from treescript_builder.data.tree_data import TreeData
from treescript_builder.input.string_validation import validate_data_label


_DATA_DIR_PATH_DOES_NOT_EXIST_MSG = 'Data Directory Does Not Exist.'
_DATA_DIR_NOT_PROVIDED_FOR_DATA_LABEL_MSG = 'No DataDirectory provided, but DataLabel found on Line: '

_DATA_LABEL_INVALID_MSG = 'Invalid Data Label on line: '
_DATA_LABEL_DUPLICATE_MSG = 'Duplicate DataLabels Are Not Allowed In This Operation. Found Duplicate on Line: '
_DATA_LABEL_NOT_FOUND_MSG = 'Label not found in DataDirectory on Line: '
_DATA_FILE_EXISTS_MSG = 'Data File already exists on Line: '


def _validate_node_data_label(node: TreeData) -> str | None:
    if node.data_label == '': # For compatibility with 0.1.x
        return None
    if not validate_data_label(data_label := node.get_data_label()):
        exit(_DATA_LABEL_INVALID_MSG + str(node.line_number))
    return data_label


class DataDirectory:
    """ Manages Access to the Data Directory.
 - Search for a Data Label, and obtain the Path to the Data File.

**Method Summary:**
 - validate_build(TreeData): Path?
 - validate_trim(TreeData): Path?
    """

    def __init__(self, data_dir: Path):
        if not isinstance(data_dir, Path):
            raise TypeError
        elif not data_dir.exists():
            exit(_DATA_DIR_PATH_DOES_NOT_EXIST_MSG)
        self._data_dir: Path = data_dir
        self._expected_trim_data: list[str] = []

    def validate_build(self, node: TreeData) -> Path | None:
        """ Determine if the Data File supporting this Tree node is available.

**Parameters:**
 - node (TreeData): The TreeData to validate.

**Returns:**
 Path? - The Path to the Data File in the Data Directory.

**Raises:**
 SystemExit - When the Data label is invalid, or the Data File does not exist.
        """
        if (data_label := _validate_node_data_label(node)) is None:
            return None
        # Search in the DataDir for this DataFile.
        if (data_path := self._search_label(data_label)) is None:
            exit(_DATA_LABEL_NOT_FOUND_MSG + str(node.line_number))
        return data_path

    def validate_trim(self, node: TreeData) -> Path | None:
        """ Determine if the File already exists in the Data Directory.

**Parameters:**
 - node (TreeData): The TreeData to validate.

**Returns:**
 Path? - The Path to a new File in the Data Directory.

**Raises:**
 SystemExit - When the Data label is invalid, or the Data File already exists.
        """
        if (data_label := _validate_node_data_label(node)) is None:
            return None
        # Check if another TreeData Node has this DataLabel
        if data_label in self._expected_trim_data:
            exit(_DATA_LABEL_DUPLICATE_MSG + str(node.line_number))
        # Check if the DataFile already exists
        if self._search_label(data_label) is not None:
            exit(_DATA_FILE_EXISTS_MSG + str(node.line_number))
        # Add the new DataLabel to the collection
        self._expected_trim_data.append(data_label)
        # Return the DataLabel Path
        return self._data_dir / data_label

    def _search_label(self, data_label: str) -> Path | None:
        """ Search for a DataLabel in this DataDirectory.

**Parameters:**
 - data_label (str): The DataLabel to search for.

**Returns:**
 Path? - The Path to the DataFile, or None.
        """
        try:
            return next(self._data_dir.glob(data_label))
        except StopIteration:
            return None
        except OSError:
            return None


def get_data_dir_validator(
    data_dir: DataDirectory | None,
    is_trim: bool,
) -> Callable[[TreeData], Path | None]:
    """ Obtain a Method that Validates incoming TreeData Nodes for the given DataDirectory conditions.
 - When DataDirectory is not present, there should be no DataLabels on any Nodes.

**Parameters:**
 - data_dir (DataDirectory?): The DataDirectory object to be used by the Validator Method. If None, ensures no TreeData have DataLabels.
 - is_trim (bool): Whether the Validation is for Trim operation.

**Returns:**
 Callable[[TreeData], Path?] - A Method that (optionally wraps a DataDirectory) transforms TreeData to DataFile Paths.

**Raises:**
 SystemExit - When there is a DataLabel on a Node, and no DataDirectory is associated with the Validator Method.
    """
    if data_dir is None:
        def _raise_if_data_label_present(node: TreeData):
            if node.data_label != '':
                exit(_DATA_DIR_NOT_PROVIDED_FOR_DATA_LABEL_MSG + str(node.line_number))
            return None
        return _raise_if_data_label_present
    if is_trim:
        return lambda node: data_dir.validate_trim(node)
    return lambda node: data_dir.validate_build(node)
