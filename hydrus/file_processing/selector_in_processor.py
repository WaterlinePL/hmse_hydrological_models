import math
from dataclasses import dataclass

from hmse_simulations.hmse_projects.hmse_hydrological_models.hydrus.file_processing.text_file_processor import \
    TextFileProcessor


@dataclass
class SelectorInProcessor(TextFileProcessor):

    def update_initial_and_final_step(self, first_step: int, step_count: int):
        self._reset()
        line = self.fp.readline()
        while line:
            if line.strip().startswith("tInit"):
                line_start = self.fp.tell()
                line_with_step_data = self.fp.readline()
                time_step_data = line_with_step_data.split()
                t_init, t_max = time_step_data[0], time_step_data[1]
                new_t_init = float(t_init) + first_step
                new_t_max = math.ceil(new_t_init + step_count)
                new_line = TextFileProcessor._substitute_in_line(line_with_step_data, new_t_init, col_idx=0)
                new_line = TextFileProcessor._substitute_in_line(new_line, new_t_max, col_idx=1)
                self.fp.seek(line_start)
                self.fp.write(new_line)
                break

            line_start_ptr = self.fp.tell()
            line = self.fp.readline()
