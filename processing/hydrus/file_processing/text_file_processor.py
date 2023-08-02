from abc import ABC
from dataclasses import dataclass
from typing import List

import numpy as np
from typing.io import TextIO

from .. import hydrus_number_formatter
from ..hydrus_number_formatter import FloatFormat
from ... import julian_calendar_manager


@dataclass
class TextFileProcessor(ABC):
    fp: TextIO  # Should be opened and closed outside the class, should be read-write

    def _reset(self):
        self.fp.seek(0)

    @staticmethod
    def _substitute_in_line(line: str, value: float, col_idx: int,
                            float_format: FloatFormat = FloatFormat.THREE_DIGITS_AFTER_DOT) -> str:
        cols = TextFileProcessor._split_into_columns(line)
        formatted_new_val = hydrus_number_formatter.format_swapped_float(value, val_format=float_format)
        cols[col_idx] = formatted_new_val
        return '\t'.join(cols) + '\n'

    @staticmethod
    def _rewrite_line_to_julian(line: str) -> str:
        julian_day_val = julian_calendar_manager.float_to_julian(float(line.split()[0]))
        return TextFileProcessor._substitute_in_line(line, julian_day_val, col_idx=0)

    @staticmethod
    def _read_value_from_col(line: str, col_idx: int):
        i = -1
        current_value = None
        value_start_idx = -1

        parts = line.replace('\t', ' ').split(' ')
        for p in parts:
            value_start_idx += 1
            if len(p) > 0:
                i += 1
                if i == col_idx:
                    current_value = p
                    break
                else:
                    value_start_idx += len(p)
        return current_value, value_start_idx

    @staticmethod
    def _split_into_columns(line: str) -> List[str]:
        return line.split()
