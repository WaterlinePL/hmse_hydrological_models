from abc import abstractmethod
from dataclasses import dataclass
from typing import List, Tuple, Callable, Optional

from hmse_simulations.hmse_projects.hmse_hydrological_models.hydrus.file_processing.text_file_processor import \
    TextFileProcessor


@dataclass
class LineByLineProcessor(TextFileProcessor):

    @abstractmethod
    def truncate_file(self, data_start_idx: int, data_count: int):
        ...

    def _perform_truncating(self, data_content_line_prefix: str, total_record_count_line_prefix: str,
                            data_start_idx: int, data_count: int,
                            rewrite_func: Optional[Callable[[str], str]] = None) -> Tuple[float, float]:
        lines, data_start, total_data_records = self._preparse_lines(data_content_line_prefix,
                                                                     total_record_count_line_prefix)

        return self._save_sliced_data(lines, data_start, total_data_records, data_start_idx, data_count,
                                      rewrite_func)

    def _preparse_lines(self, data_content_line_prefix: str,
                        total_record_count_line_prefix: str) -> Tuple[List[str], int, int]:

        lines = self.fp.readlines()
        total_data_records = 0
        data_start = -1

        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith(total_record_count_line_prefix):
                total_data_records = int(lines[i + 1].strip().split(' ')[0].strip())
            elif stripped.startswith(data_content_line_prefix):
                data_start = i + 1

        self._reset()
        return lines, data_start, total_data_records

    def _save_sliced_data(self, lines: List[str], data_start: int, total_data_records: int,
                          record_start_idx: int, record_count: int,
                          rewrite_func: Optional[Callable[[str], str]]) -> Tuple[float, float]:

        new_data_start = data_start + record_start_idx
        new_data_end = new_data_start + record_count
        data_end = data_start + total_data_records

        first_original_data_time_step = None
        first_data_time_step = None
        last_data_time_step = None
        use_rewrite = False

        for i, line in enumerate(lines):
            # Truncate only data section of a file
            if i < data_start or new_data_start <= i < new_data_end or i >= data_end:
                to_write = line
                if new_data_start <= i < new_data_end:
                    if first_original_data_time_step is None:
                        first_original_data_time_step = float(line.split()[0])
                        use_rewrite = first_original_data_time_step > 365
                    if rewrite_func and use_rewrite:
                        to_write = rewrite_func(line)
                    cur_time_step = float(to_write.split()[0])
                    if first_data_time_step is None:
                        first_data_time_step = cur_time_step
                    last_data_time_step = cur_time_step
                self.fp.write(to_write)

        self.fp.truncate()
        self._reset()
        return first_data_time_step, last_data_time_step
