import json
import os
import shutil
from typing import Dict, Tuple

from . import hydrus_utils
from .file_processing.atmosph_in_processor import AtmosphInProcessor
from .file_processing.meteo_in_processor import MeteoInProcessor
from .file_processing.nod_inf_out_processor import NodInfOutProcessor
from .file_processing.profile_dat_processor import ProfileDatProcessor
from .file_processing.selector_in_processor import SelectorInProcessor
from .hydrus_profile_pressure_calculator import calculate_pressure_for_hydrus_model
from ..local_fs_configuration import local_paths
from ..local_fs_configuration.feedback_loop_file_management import find_previous_simulation_step_dir
from ..unit_manager import LengthUnit


def prepare_model_for_next_iteration(project_id: str, ref_hydrus_id: str, compound_hydrus_id: str, spin_up: int):
    ref_hydrus_dir = local_paths.get_hydrus_model_path(project_id, ref_hydrus_id, simulation_mode=False)
    prev_sim_step_dir = find_previous_simulation_step_dir(project_id)

    prev_hydrus_dir = os.path.join(prev_sim_step_dir, 'hydrus',
                                   compound_hydrus_id) if prev_sim_step_dir else None  # FIXME: kind of bad
    new_hydrus_dir = local_paths.get_hydrus_model_path(project_id, compound_hydrus_id, simulation_mode=True)

    metadata_path = local_paths.get_project_metadata_path(project_id)
    with open(metadata_path, 'r', encoding='utf-8') as fp:
        project_metadata = json.load(fp)

    step = 0 if not prev_sim_step_dir else int(prev_sim_step_dir.split('_')[-1]) + 1
    __create_temporary_model(ref_hydrus_dir=ref_hydrus_dir,
                             prev_hydrus_dir=prev_hydrus_dir,
                             new_hydrus_dir=new_hydrus_dir,
                             project_metadata=project_metadata,
                             step=step,
                             spin_up=spin_up)


def update_bottom_pressure(project_id: str,
                           hydrus_id: str,
                           btm_pressure_val: float) -> None:
    model_dir = local_paths.get_hydrus_model_path(project_id, hydrus_id, simulation_mode=True)
    profile_dat_path = hydrus_utils.find_hydrus_file_path(model_dir, file_name="profile.dat")
    new_pressure_in_profile = calculate_pressure_for_hydrus_model(model_dir, btm_pressure=btm_pressure_val)
    with open(profile_dat_path, 'r+', encoding="utf-8") as fp:
        ProfileDatProcessor(fp).swap_pressure(new_pressure_in_profile)


def get_profile_depth(project_id: str, hydrus_id: str) -> Tuple[float, LengthUnit]:
    model_dir = local_paths.get_hydrus_model_path(project_id, hydrus_id, simulation_mode=True)
    hydrus_info_file_path = hydrus_utils.find_hydrus_file_path(model_dir, file_name="hydrus1d.dat")
    with open(hydrus_info_file_path, 'r', encoding='utf-8') as fp:
        unit = None
        depth = None
        for line in fp.readlines():
            if line.startswith("SpaceUnit"):
                unit = line.split('=')[1].strip()
            elif line.startswith("ProfileDepth"):
                depth = float(line.split('=')[1])
        return depth, LengthUnit(unit)


def __create_temporary_model(ref_hydrus_dir: str, prev_hydrus_dir: str, new_hydrus_dir: str,
                             project_metadata: Dict, step: int, spin_up: int) -> None:
    shutil.rmtree(new_hydrus_dir, ignore_errors=True)
    shutil.copytree(ref_hydrus_dir, new_hydrus_dir)

    # Initial conditions from previous iteration
    if prev_hydrus_dir:
        nod_inf_path = hydrus_utils.find_hydrus_file_path(prev_hydrus_dir, file_name="nod_inf.out")
        with open(nod_inf_path, 'r', encoding='utf-8') as fp:
            prev_node_pressure = NodInfOutProcessor(fp).read_node_pressure()

        profile_dat_path = hydrus_utils.find_hydrus_file_path(new_hydrus_dir, file_name="profile.dat")
        with open(profile_dat_path, 'r+', encoding='utf-8') as fp:
            ProfileDatProcessor(fp).swap_pressure(prev_node_pressure)

        prev_iter_t_level_out = hydrus_utils.find_hydrus_file_path(prev_hydrus_dir, file_name="t_level.out")
        new_t_level_out = (hydrus_utils.find_hydrus_file_path(new_hydrus_dir, file_name="t_level.out")
                           or os.path.join(new_hydrus_dir, "T_Level.out"))
        shutil.copy(prev_iter_t_level_out, new_t_level_out)

    # Crop packages to match Modflow timestep
    first_step, step_count = __get_hydrus_time_range(project_metadata, step, spin_up)

    atmosph_in_path = hydrus_utils.find_hydrus_file_path(new_hydrus_dir, file_name="atmosph.in")
    with open(atmosph_in_path, 'r+', encoding='utf-8') as fp:
        atmo_first_jul_day, atmo_last_jul_day = AtmosphInProcessor(fp).truncate_file(first_step, step_count)

    meteo_in_path = hydrus_utils.find_hydrus_file_path(new_hydrus_dir, file_name="meteo.in")
    with open(meteo_in_path, 'r+', encoding='utf-8') as fp:
        meteo_first_jul_day, meteo_last_jul_day = MeteoInProcessor(fp).truncate_file(first_step, step_count)

    if atmo_first_jul_day != meteo_first_jul_day or atmo_last_jul_day != meteo_last_jul_day:
        raise RuntimeError(f"ATMPOSH.IN and METEO.IN record ranges do not match: "
                           f"ATMOSPH.IN: ({atmo_first_jul_day}, {atmo_last_jul_day}) "
                           f"METEO.IN: ({meteo_first_jul_day}, {meteo_last_jul_day})")

    first_record_day = meteo_first_jul_day
    last_record_day = meteo_last_jul_day
    selector_in_path = hydrus_utils.find_hydrus_file_path(new_hydrus_dir, file_name="selector.in")
    with open(selector_in_path, 'r+', encoding='utf-8') as fp:
        selector_in_processor = SelectorInProcessor(fp)
        selector_in_processor.update_initial_and_final_step(first_record_day, last_record_day)


def __get_hydrus_time_range(project_metadata: Dict, step: int, spin_up: int) -> Tuple[int, int]:
    steps_info = project_metadata["modflow_metadata"]["steps_info"]
    first_step = 0
    step_count = 0
    i = -1

    for info in steps_info:
        i += 1
        if i == step:
            step_count = info["duration"]
            break
        else:
            first_step += info["duration"]

    if step == 0:
        step_count += spin_up
    else:
        first_step += spin_up

    return first_step, step_count
