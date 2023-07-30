import re
from dataclasses import dataclass
from typing import List, Union

from .text_file_processor import TextFileProcessor


class UnknownProfileDatFormat(RuntimeError):
    pass


@dataclass
class ProfileDatProcessor(TextFileProcessor):

    def read_profile_depth(self) -> float:
        self._reset()
        lines = self.fp.readlines()
        for i, l in enumerate(lines):
            match = re.match(r'\s*(\d+)\s*', l)
            if match:
                node_count = int(match[1])
                first_node_line = lines[i + 1]
                last_node_line = lines[i + node_count]
                first_node_coord = float(first_node_line.split()[1])
                last_node_coord = float(last_node_line.split()[1])
                return first_node_coord - last_node_coord
        raise UnknownProfileDatFormat("Could not read the profile depth from Profile.dat file!")

    def swap_pressure(self, pressure: Union[List[float], float]):
        """
        @param pressure: List of pressure vals or single value at the bottom
        @return:
        """

        self._reset()

        swap_only_at_bottom = isinstance(pressure, float)
        profile_info_entries = None
        profile_info_counter = 0

        # line_start_ptr = self.fp.tell()
        # line = self.fp.readline()
        # while line:
        #     line = line.replace('\t', ' ')
        #     if profile_info_entries is None and 'x' in line and 'h' in line:
        #         profile_info_entries = int(line.strip().split()[0])
        #     elif profile_info_entries is not None and profile_info_counter < profile_info_entries:
        #
        #         if swap_only_at_bottom and profile_info_counter == profile_info_entries - 1:
        #             new_line = TextFileProcessor._substitute_in_line(line, pressure, col_idx=2)
        #             self.fp.seek(line_start_ptr)
        #             self.fp.write(new_line)
        #             break
        #         elif not swap_only_at_bottom:
        #             new_line = TextFileProcessor._substitute_in_line(line, pressure[profile_info_counter], col_idx=2)
        #             self.fp.seek(line_start_ptr)
        #             self.fp.write(new_line)
        #         profile_info_counter += 1
        #
        #     line_start_ptr = self.fp.tell()
        #     line = self.fp.readline()
        lines = self.fp.readlines()
        for i, line in enumerate(lines):
            if profile_info_entries is None and 'x' in line and 'h' in line:
                profile_info_entries = int(line.strip().split()[0])
            elif profile_info_entries is not None and profile_info_counter < profile_info_entries:

                if swap_only_at_bottom and profile_info_counter == profile_info_entries - 1:
                    new_line = TextFileProcessor._substitute_in_line(line, pressure, col_idx=2)
                    lines[i] = new_line
                    break
                elif not swap_only_at_bottom:
                    new_line = TextFileProcessor._substitute_in_line(line, pressure[profile_info_counter], col_idx=2)
                    lines[i] = new_line
                profile_info_counter += 1

        self._reset()
        self.fp.writelines(lines)
        self.fp.truncate()
