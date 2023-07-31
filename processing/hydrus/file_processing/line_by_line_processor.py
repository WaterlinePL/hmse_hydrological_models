from abc import abstractmethod
from dataclasses import dataclass
from typing import List, Tuple, Callable, Optional

from .text_file_processor import TextFileProcessor
from ... import julian_calendar_manager


@dataclass
class LineByLineProcessor(TextFileProcessor):

    @abstractmethod
    def truncate_file(self, data_start_idx: int, data_count: int):
        ...

    def _perform_truncating(self, data_content_line_prefix: str, total_record_count_line_prefix: str,
                            data_start_idx: int, data_count: int) -> Tuple[float, float]:
        lines, data_start, total_data_records = self._preparse_lines(data_content_line_prefix,
                                                                     total_record_count_line_prefix)

        return self._save_sliced_data(lines, data_start, total_data_records, data_start_idx, data_count)

    def _preparse_lines(self, data_content_line_prefix: str,
                        total_record_count_line_prefix: str) -> Tuple[List[str], int, int]:

        lines = self.fp.readlines()
        total_data_records = 0
        data_start = -1

        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith(total_record_count_line_prefix):
                total_data_records = int(lines[i + 1].strip().split()[0].strip())
            elif stripped.startswith(data_content_line_prefix):
                data_start = i + 1

        self._reset()
        return lines, data_start, total_data_records

    def _save_sliced_data(self, lines: List[str], data_start: int, total_data_records: int,
                          record_start_idx: int, record_count: int) -> Tuple[float, float]:

        new_data_start = data_start + record_start_idx
        new_data_end = new_data_start + record_count
        data_end = data_start + total_data_records

        first_original_data_time_step = None
        first_data_time_step = None
        last_data_time_step = None

        lines_to_write = []
        julian_iter = -1

        for i, line in enumerate(lines):
            # Truncate only data section of a file
            if i < data_start or new_data_start <= i < new_data_end or i >= data_end:
                to_write = line
                if new_data_start <= i < new_data_end:
                    if first_original_data_time_step is None:
                        first_original_data_time_step = float(line.split()[0])
                        julian_iter = julian_calendar_manager.float_to_julian(first_original_data_time_step)
                    if julian_iter >= 0:
                        to_write = TextFileProcessor._substitute_in_line(line, julian_iter, col_idx=0)
                        julian_iter += 1
                    cur_time_step = float(to_write.split()[0])
                    if first_data_time_step is None:
                        first_data_time_step = cur_time_step
                    last_data_time_step = cur_time_step
                lines_to_write.append(to_write)

        self.fp.truncate()
        self.fp.writelines(lines_to_write)
        self._reset()
        return first_data_time_step, last_data_time_step
