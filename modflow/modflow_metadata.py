from dataclasses import dataclass, field
from typing import List

from hmse_projects.hmse_hydrological_models.typing_help import ModflowID


@dataclass
class ModflowMetadata:
    modflow_id: ModflowID
    rows: int
    cols: int
    grid_unit: str  # Maybe enum
    duration: int   # Days
    row_cells: List[float] = field(default_factory=list)
    col_cells: List[float] = field(default_factory=list)

    def to_json(self):
        return self.__dict__
