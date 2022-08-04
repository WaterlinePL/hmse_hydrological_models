from dataclasses import dataclass
from typing import List


@dataclass
class ModflowMetadata:
    rows: int
    cols: int
    row_cells: List[float]
    col_cells: List[float]
    grid_unit: str  # Maybe enum
