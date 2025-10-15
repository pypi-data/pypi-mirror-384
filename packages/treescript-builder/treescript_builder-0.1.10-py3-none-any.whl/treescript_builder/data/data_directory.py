""" Data Directory Management.
 Author: DK96-OS 2024 - 2025
"""
from pathlib import Path
from sys import exit

from treescript_builder.data.tree_data import TreeData
from treescript_builder.input.string_validation import validate_data_label


class DataDirectory:
    """ Manages Access to the Data Directory.
 - Search for a Data Label, and obtain the Path to the Data File.

**Method Summary:**
 - validate_build(TreeData): Path?
 - validate_trim(TreeData): Path?
    """

    def __init__(self, data_dir: Path):
        if not isinstance(data_dir, Path) or not data_dir.exists():
            exit('The Data Directory must be a Path that Exists!')
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
        if node.data_label == '': # For compatibility with 0.1.x
            return None
        if not validate_data_label(data_label := node.get_data_label()):
            exit(f'Invalid Data Label on line: {node.line_number}')
        # Search in the DataDir for this Data File.
        if (data_path := self._search_label(data_label)) is None:
            exit(f'Label ({node.data_label}) not found in DataDirectory on Line: {node.line_number}')
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
        if node.data_label == '': # For compatibility with 0.1.x
            return None
        if not validate_data_label(data_label := node.get_data_label()):
            exit(f'Invalid Data Label on line: {node.line_number}')
        # Check if another TreeData Node has this DataLabel
        if data_label in self._expected_trim_data:
            exit(f"Duplicate DataLabels in Trim Operation on Line: {node.line_number}")
        # Check if the Data File already exists
        if self._search_label(data_label) is not None:
            exit(f'Data File already exists!\n({data_label}) on Line: {node.line_number}')
        # Add the new DataLabel to the collection
        self._expected_trim_data.append(data_label)
        # Return the DataLabel Path
        return self._data_dir / data_label

    def _search_label(self, data_label: str) -> Path | None:
        """ Search for a Data Label in this Data Directory.

**Parameters:**
 - data_label (str): The Data Label to search for.

**Returns:**
 Path? - The Path to the Data File, or None.
        """
        # Find the Data Label File
        data_files = self._data_dir.glob(data_label)
        try:
            return next(data_files)
        except StopIteration:
            return None
        except OSError:
            return None
