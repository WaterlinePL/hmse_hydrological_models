import logging
import os
from typing import List

EXPECTED_INPUT_FILES = ["SELECTOR.IN", "ATMOSPH.IN"]


def get_hydrus_input_files(model_path: str) -> List[str]:
    return [file.lower() for file in os.listdir(model_path) if file.lower().endswith(".in")]


def validate_model(model_path: str):
    input_files = get_hydrus_input_files(model_path)
    for expected_file in EXPECTED_INPUT_FILES:
        if expected_file.lower() not in input_files:
            return False
    return True


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
