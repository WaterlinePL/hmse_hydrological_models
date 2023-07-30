# Take care about stuff like: 0.000000e+000 and 000.000
import re
from typing import Tuple

from .file_processing.exceptions import UnsupportedFloatFormat


# Returns string and offset
def format_swapped_float(value: float) -> str:
    if value < 1000:
        return f'{{:.3f}}'.format(value)
    else:
        digits_after_dot = 5
        base = f'{{:.{digits_after_dot}e}}'.format(value)  # '4.08000e+10'
        base_parts = base.split('e')
        power = int(base_parts[1])  # TODO: is this needed?
        return f"{base_parts[0]}e{'+' if power >= 0 else '-'}{abs(power):03}"
