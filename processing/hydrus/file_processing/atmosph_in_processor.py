from dataclasses import dataclass
from typing import Tuple

from .line_by_line_processor import LineByLineProcessor
from .text_file_processor import TextFileProcessor


@dataclass
class AtmosphInProcessor(LineByLineProcessor):

    def truncate_file(self, data_start_idx: int, data_count: int) -> Tuple[float, float]:
        return self._perform_truncating(data_content_line_prefix="tAtm",
                                        total_record_count_line_prefix="MaxAL",
                                        data_start_idx=data_start_idx,
                                        data_count=data_count)
