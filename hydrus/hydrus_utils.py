import logging
import os
from collections import defaultdict
from typing import List, Union, Optional, Dict, Tuple
from zipfile import ZipFile

from ..local_fs_configuration import path_constants
from ..model_exceptions import HydrusMissingFileError

EXPECTED_INPUT_FILES = ["SELECTOR.IN", "ATMOSPH.IN"]


def get_hydrus_input_files(model_path: Union[os.PathLike, str]) -> List[str]:
    return [file.casefold() for file in os.listdir(model_path) if file.lower().endswith(".in")]


def get_hydrus_to_shapes_mapping(shapes_to_hydrus: Dict[str, Union[str, float]]) -> Dict[str, List[str]]:
    hydrus_to_shapes = defaultdict(list)
    for shape_id, hydrus_id in shapes_to_hydrus.items():
        if isinstance(hydrus_id, str):
            hydrus_to_shapes[hydrus_id].append(shape_id)
    return hydrus_to_shapes


def get_compound_hydrus_ids_for_feedback_loop(shapes_to_hydrus: Dict[str, Union[str, float]]) -> List[Tuple[str, str]]:
    return [(hydrus_id, path_constants.get_feedback_loop_hydrus_name(hydrus_id, shape_id))
            for shape_id, hydrus_id in shapes_to_hydrus.items()
            if isinstance(hydrus_id, str)]


def get_hydrus_mapping_for_transfer_to_modflow(shapes_to_hydrus: Dict[str, Union[str, float]],
                                               use_compound_hydrus_ids: bool = False) -> Dict[str, List[str]]:
    transfer_mapping = defaultdict(list)
    for shape_id, hydrus_id in shapes_to_hydrus.items():
        if isinstance(hydrus_id, str) and use_compound_hydrus_ids:
            transfer_mapping[path_constants.get_feedback_loop_hydrus_name(hydrus_id, shape_id)].append(shape_id)
        else:
            transfer_mapping[hydrus_id].append(shape_id)
    return transfer_mapping


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




# Files: PROFILE.DAT, etc.
def find_hydrus_file_path(hydrus_base_dir: str, file_name: str) -> Optional[str]:
    file = next(f for f in os.listdir(hydrus_base_dir) if f.lower() == file_name.lower())
    return os.path.join(hydrus_base_dir, file) if file else None
