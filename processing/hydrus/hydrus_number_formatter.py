# Take care about stuff like: 0.000000e+000 and 000.000
import re
from typing import Tuple

from .file_processing.exceptions import UnsupportedFloatFormat


# Returns string and offset
def format_swapped_float(value: float, swapped_sample_format: str) -> Tuple[str, int]:
    if re.match(r'-?\d\.(\d+)e(-|\+)(\d+)', swapped_sample_format):
        m = re.match(r'-?\d\.(\d+)e(-|\+)(\d+)', swapped_sample_format)
        digits_after_dot = len(m[1])
        base = f'{{:.{digits_after_dot}e}}'.format(value)   # '4.08000e+10'
        base_parts = base.split('e')
        power = int(base_parts[1])
        return f"{base_parts[0]}e{'+' if power >= 0 else '-'}{abs(power):03}", 0
    elif re.match(r'\d+(\.\d+)?', swapped_sample_format):   # Currently only for SELECTOR.IN
        number_parts = swapped_sample_format.split('.')
        after_dot = number_parts[1] if len(number_parts) > 1 else None
        if after_dot is not None:
            without_padding = f'{{:.{len(after_dot)}f}}'.format(value)
        else:
            without_padding = str(int(value))
        offset = len(swapped_sample_format) - len(without_padding)
        if offset > 0:
            return f"{' ' * offset}{without_padding}", 0
        return without_padding, offset
    else:
        raise UnsupportedFloatFormat(f"Unsupported file format present in number: {swapped_sample_format}")
