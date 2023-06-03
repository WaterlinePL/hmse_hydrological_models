import copy
from dataclasses import dataclass, field
from typing import List

from .modflow_step import ModflowStep, ModflowStepType
from ..unit_manager import LengthUnit
from ..typing_help import ModflowID


@dataclass
class ModflowMetadata:
    modflow_id: ModflowID
    rows: int
    cols: int
    grid_unit: LengthUnit
    steps_info: List[ModflowStep]
    row_cells: List[float] = field(default_factory=list)
    col_cells: List[float] = field(default_factory=list)

    def __post_init__(self):
        new_step_info = []
        should_swap = False
        for step in self.steps_info:
            if isinstance(step, dict):
                should_swap = True
                new_step_info.append(ModflowStep(**step))

        if should_swap:
            self.steps_info = new_step_info

    def to_json(self):
        steps_info = copy.deepcopy(self.steps_info)
        self.steps_info = [info.__dict__ for info in self.steps_info]
        serialized = copy.deepcopy(self.__dict__)
        self.steps_info = steps_info
        serialized["duration"] = self.get_duration()
        return serialized

    def get_duration(self) -> int:
        return sum(map(lambda info: info.duration if info.type == ModflowStepType.TRANSIENT else 0,
                       self.steps_info))
