"""The Instruction Data in a Tree Operation.
 Author: DK96-OS 2024 - 2025
"""
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class InstructionData:
    """ The Data required to execute the Instruction.

**Fields:**
 - is_dir (bool): Whether the Instruction relates to a Directory.
 - path (Path): The Path of the Instruction.
 - data_path (Path?): The Data Directory Path of the Instruction, if applicable. Default: None.
    """
    is_dir: bool
    path: Path
    data_path: Path | None = None