import re
from dataclasses import dataclass
from typing import Dict

import pandas as pd

from .text_file_processor import TextFileProcessor
from ..hydrus_number_formatter import FloatFormat
from ...unit_manager import LengthUnit


@dataclass
class SelectorInProcessor(TextFileProcessor):

    def get_model_length(self) -> LengthUnit:
        self._reset()
        lines = self.fp.readlines()
        for i, line in enumerate(lines):
            if "LUnit" in line:
                unit = lines[i + 1].strip().split()[0].strip()
                return LengthUnit(unit)
        raise RuntimeError(f"Invalid data, no length unit found file ({self.fp.name})")

    def update_initial_and_final_step(self, first_day: float, last_day: float):
        self._reset()
        lines = self.fp.readlines()
        for i, line in enumerate(lines):
            to_write = line
            write_idx = i
            if line.strip().endswith("MPL"):
                line_with_node_information = lines[i + 1]
                to_write = TextFileProcessor._substitute_in_line(line_with_node_information, 1, col_idx=7,
                                                                 float_format=FloatFormat.INTEGER)
                write_idx = i + 1
            elif line.strip().startswith("tInit"):
                line_with_step_data = lines[i + 1]
                new_t_init = first_day - 0.1
                new_t_max = last_day - 0.1
                new_line = TextFileProcessor._substitute_in_line(line_with_step_data, new_t_init, col_idx=0)
                to_write = TextFileProcessor._substitute_in_line(new_line, new_t_max, col_idx=1)
                write_idx = i + 1
            elif line.strip().startswith("TPrint(1)"):
                line_with_print_node_information_config = lines[i + 1]
                to_write = TextFileProcessor._substitute_in_line(line_with_print_node_information_config,
                                                                 last_day - 0.01, col_idx=0)
                write_idx = i + 1
            if to_write[-1] != '\n':
                to_write = to_write + '\n'
            lines[write_idx] = to_write

        self._reset()
        self.fp.writelines(lines)
        self.fp.truncate()

    def read_waterflow_config(self) -> Dict:
        self._reset()
        lines = self.fp.readlines()
        block = None

        for i, line in enumerate(lines):
            block_match = re.search(r'(?<=BLOCK )[A-G](?=:)', line)
            if block_match:
                block = block_match[0].strip()
                continue
            if block == "B" and "Model" in line:
                iModel = lines[i + 1].strip().split()[0].strip()
                return {"iModel": int(iModel)}
        raise RuntimeError(f"Invalid data, water iModel specified in ({self.fp.name})")

    def read_material_properties(self) -> pd.DataFrame:
        self._reset()
        lines = self.fp.readlines()
        block = None
        materials_found = False
        material_properties = []

        for i, line in enumerate(lines):
            block_match = re.search(r'(?<=BLOCK )[A-G](?=:)', line)
            if block_match:
                block = block_match[0].strip()
                continue
            if block == "B" and "thr" in line:
                materials_found = True
                continue

            if materials_found:
                if block != "B":
                    return pd.DataFrame(material_properties)

                if re.search(r'\d', line):
                    # material data line
                    m_props = list(map(float, line.strip().split()))
                    material_properties.append(m_props)
                else:
                    return pd.DataFrame(material_properties)
        raise RuntimeError(f"Invalid data, water iModel specified in ({self.fp.name})")
