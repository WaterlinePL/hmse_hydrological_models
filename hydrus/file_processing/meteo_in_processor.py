from dataclasses import dataclass

from .line_by_line_processor import LineByLineProcessor


@dataclass
class MeteoInProcessor(LineByLineProcessor):

    def truncate_file(self, data_start_idx: int, data_count: int):
        self._perform_truncating(data_content_line_prefix="[T]",
                                 total_record_count_line_prefix="MeteoRecords",
                                 data_start_idx=data_start_idx,
                                 data_count=data_count)
