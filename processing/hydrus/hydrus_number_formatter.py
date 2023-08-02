# Take care about stuff like: 0.000000e+000 and 000.000
from enum import auto

from strenum import StrEnum

from .file_processing.exceptions import UnsupportedFloatFormat


class FloatFormat(StrEnum):
    SCIENTIFIC = auto()
    THREE_DIGITS_AFTER_DOT = auto()
    INTEGER = auto()


# Returns string and offset
def format_swapped_float(value: float, val_format: FloatFormat) -> str:
    if val_format == FloatFormat.THREE_DIGITS_AFTER_DOT:
        return f"{{:.3f}}".format(value)
    elif val_format == FloatFormat.SCIENTIFIC:
        digits_after_dot = 5
        base = f'{{:.{digits_after_dot}e}}'.format(value)  # '4.08000e+10'
        base_parts = base.split('e')
        power = int(base_parts[1])  # TODO: is this needed?
        return f"{base_parts[0]}e{'+' if power >= 0 else '-'}{abs(power):03}"
    elif val_format == FloatFormat.INTEGER:
        return str(int(value))
    else:
        raise UnsupportedFloatFormat("Unknown float format!")
