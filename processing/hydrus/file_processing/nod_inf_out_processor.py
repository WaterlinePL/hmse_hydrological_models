import re
from dataclasses import dataclass
from typing import List

from .text_file_processor import TextFileProcessor


@dataclass
class NodInfOutProcessor(TextFileProcessor):

    def read_node_pressure(self) -> List[float]:
        pressure_data = []
        for line in self.fp.readlines():
            if line.strip().startswith("[L]"):
                pressure_data = []
            elif re.match(r'^\d+ ', line.strip()):
                pressure_value, _ = TextFileProcessor._read_value_from_col(line, col_idx=2)
                pressure_data.append(float(pressure_value))
        return pressure_data
