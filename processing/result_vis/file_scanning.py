import os
from typing import Optional


def scan_for_modflow_file(model_path: str, ext: str = ".nam") -> Optional[str]:
    for file in os.listdir(model_path):
        if file.endswith(ext):
            return file
    return None


def find_hydrus_file_path(hydrus_base_dir: str, file_name: str) -> Optional[str]:
    try:
        return os.path.join(hydrus_base_dir,
                            next(f for f in os.listdir(hydrus_base_dir) if f.lower() == file_name.lower()))
    except StopIteration:
        return None


def get_hydrus_model_length(selector_file_path: str) -> str:
    with open(selector_file_path, 'r') as fp:
        lines = fp.readlines()
        for i, line in enumerate(lines):
            if "LUnit" in line:
                return lines[i + 1].strip().split()[0].strip()
