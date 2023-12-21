import logging
import os
from collections import defaultdict
from typing import List, Union, Optional, Dict, Tuple, Set
from zipfile import ZipFile

from ..local_fs_configuration import path_constants
from ..model_exceptions import HydrusMissingFileError

EXPECTED_INPUT_FILES = ["SELECTOR.IN", "ATMOSPH.IN"]
HYDRUS_PROPER_CASING = {
    "meteo.in": "METEO.IN",
    "atmosph.in": "ATMOSPH.IN",
    "selector.in": "SELECTOR.IN",
    "options.in": "OPTIONS.IN",
    "hysteresis.in": "HYSTERESIS.IN",
    "mater.in": "MATER.IN",
    "moistdep.in": "MOISTDEP.IN",

    "profile.dat": "PROFILE.DAT",

    "solutex.out": "SOLUTEX.OUT",
    "nod_inf_v.out": "NOD_INF_V.OUT",
    "t_level1.out": "T_LEVEL1.OUT",
    "profile.out": "PROFILE.OUT",
    "obs_node.out": "OBS_NODE.OUT",
    "balance.out": "BALANCE.OUT",
    "nod_inf.out": "NOD_INF.OUT",
    "t_level.out": "T_LEVEL.OUT",
    "run_inf.out": "RUN_INF.OUT",
    "i_check.out": "I_CHECK.OUT",
    "meteo.out": "METEO.OUT",
    "a_level.out": "A_LEVEL.OUT"
}


def get_hydrus_input_files(model_path: Union[os.PathLike, str]) -> List[str]:
    return [file.casefold() for file in os.listdir(model_path) if file.lower().endswith(".in")]


def get_used_hydrus_models(shapes_to_hydrus: Dict[str, Union[str, float]]) -> Set[str]:
    return {hydrus_id for hydrus_id in shapes_to_hydrus.values()
            if isinstance(hydrus_id, str)}


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
    os.remove(hydrus_path)
    input_files = get_hydrus_input_files(validation_dir)
    for expected_file in EXPECTED_INPUT_FILES:
        if expected_file.casefold() not in input_files:
            raise HydrusMissingFileError(description=f"Invalid Hydrus model - validation detected "
                                                     f"missing file: {expected_file}")
    __fix_hydrus_project(validation_dir)


# Files: PROFILE.DAT, etc.
def find_hydrus_file_path(hydrus_base_dir: str, file_name: str) -> Optional[str]:
    try:
        return os.path.join(hydrus_base_dir,
                            next(f for f in os.listdir(hydrus_base_dir) if f.lower() == file_name.lower()))
    except StopIteration:
        return None


def __fix_hydrus_project(hydrus_base_dir: str):
    for file in os.listdir(hydrus_base_dir):
        lowercase_file = file.lower()
        if lowercase_file not in HYDRUS_PROPER_CASING:
            logging.info(f"Skipping case-fixing for file: {file}")
            continue

        old_file = os.path.join(hydrus_base_dir, file)
        new_file = os.path.join(hydrus_base_dir, HYDRUS_PROPER_CASING[lowercase_file])
        os.rename(old_file, new_file)
        with open(new_file, 'r+b') as fp:
            original_content = fp.read()
            lf_separated_lines = original_content.replace(b'\r\n', b'\n')
            fp.seek(0)
            fp.write(lf_separated_lines)
            fp.truncate()
