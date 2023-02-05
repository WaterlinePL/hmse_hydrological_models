from dataclasses import dataclass
from enum import auto

from strenum import StrEnum


class ModflowStepType(StrEnum):
    STEADY_STATE = auto()
    TRANSIENT = auto()

    @staticmethod
    def from_bool(is_steady_state: bool) -> 'ModflowStepType':
        return ModflowStepType.STEADY_STATE if is_steady_state else ModflowStepType.TRANSIENT


@dataclass
class ModflowStep:
    type: ModflowStepType
    duration: int
