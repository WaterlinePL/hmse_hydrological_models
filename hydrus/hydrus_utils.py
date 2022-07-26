import logging
import os
from typing import List, Union
from zipfile import ZipFile

from ..model_exceptions import HydrusMissingFileError

EXPECTED_INPUT_FILES = ["SELECTOR.IN", "ATMOSPH.IN"]


def get_hydrus_input_files(model_path: Union[os.PathLike, str]) -> List[str]:
    return [file.casefold() for file in os.listdir(model_path) if file.lower().endswith(".in")]


def validate_model(hydrus_archive, validation_dir: os.PathLike):
    hydrus_path = os.path.join(validation_dir, hydrus_archive.filename)
    hydrus_archive.save(hydrus_path)
    with ZipFile(hydrus_path, 'r') as archive:
        archive.extractall(validation_dir)
        input_files = get_hydrus_input_files(validation_dir)
        for expected_file in EXPECTED_INPUT_FILES:
            if expected_file.casefold() not in input_files:
                raise HydrusMissingFileError(description=f"Invalid Hydrus model - validation detected "
                                                         f"missing file: {expected_file}")


def get_hydrus_length_unit(model_path: str):
    """
    Extracts the length unit used for a given hydrus model.

    :param model_path: the model to get the unit from
    :return: unit, string - "m", "cm" or "mm"
    """
    filepath = os.path.join(model_path, "SELECTOR.IN")
    selector_file = open(filepath, 'r')

    lines = selector_file.readlines()
    i = 0

    while True:
        if i >= len(lines):
            logging.log(logging.ERROR, f"Invalid SELECTOR.IN file for model {model_path}, no length unit found")
        curr_line = lines[i]
        if "LUnit" in curr_line:
            unit = lines[i + 1].strip()
            return unit
        i += 1
