from enum import auto

from strenum import StrEnum


class LengthUnit(StrEnum):
    mm = auto()
    cm = auto()
    m = auto()
    ft = auto()

    @staticmethod
    def map_from_alias(unit: str) -> 'LengthUnit':
        return {
            "mm": LengthUnit.mm,
            "cm": LengthUnit.cm,
            "m": LengthUnit.m,
            "meters": LengthUnit.m,
            "ft": LengthUnit.ft
        }[unit]


__INPUT_UNIT_MAPPING_MUL_COEFF = {
    LengthUnit.mm: 0.001,
    LengthUnit.cm: 0.01,
    LengthUnit.m: 1,
    LengthUnit.ft: 0.3048
}

__OUTPUT_UNIT_MAPPING_MUL_COEFF = {
    LengthUnit.mm: 1000,
    LengthUnit.cm: 100,
    LengthUnit.m: 1,
    LengthUnit.ft: 3.2808
}


def convert_units(value: float, from_unit: LengthUnit, to_unit: LengthUnit) -> float:
    if from_unit not in __INPUT_UNIT_MAPPING_MUL_COEFF:
        raise RuntimeError(f"Unknown input length unit: {from_unit}")
    if to_unit not in __INPUT_UNIT_MAPPING_MUL_COEFF:
        raise RuntimeError(f"Unknown output length unit: {to_unit}")
    return __INPUT_UNIT_MAPPING_MUL_COEFF[from_unit] * value * __OUTPUT_UNIT_MAPPING_MUL_COEFF[to_unit]
