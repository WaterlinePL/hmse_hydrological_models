import os
from typing import Dict, Union, List, Optional

import flopy
import numpy as np
import phydrus as ph

from ..hydrus import hydrus_utils, hydrus_model_management
from ..local_fs_configuration import local_paths
from ..local_fs_configuration.feedback_loop_file_management import find_previous_simulation_step_dir
from ..local_fs_configuration.path_constants import get_feedback_loop_hydrus_name
from ..modflow import modflow_utils, modflow_model_management
from ..weather_data import weather_util


class DataProcessingException(RuntimeError):
    pass


def recharge_from_hydrus_to_modflow(project_id: str,
                                    modflow_id: str,
                                    spin_up: int,  # TODO: use only if no prev step
                                    model_to_shapes_mapping: Dict[Union[str, float], List[str]],
                                    feedback_loop: bool = False) -> None:
    """
    @param model_to_shapes_mapping: Hydrus model/float value -> list of shape_id assigned to that shape
    """
    modflow_path = local_paths.get_modflow_model_path(project_id, modflow_id, simulation_mode=True)
    nam_file = modflow_utils.scan_for_modflow_file(modflow_path)

    prev_step_dir = find_previous_simulation_step_dir(project_id)
    if prev_step_dir is not None:
        spin_up = 0

    for mapping_val, assigned_shape_ids in model_to_shapes_mapping.items():
        __process_hydrus_shapes(assigned_shape_ids, mapping_val, modflow_path, nam_file,
                                project_id, spin_up, feedback_loop)


def __process_hydrus_shapes(assigned_shape_ids, mapping_val, modflow_path, nam_file,
                            project_id, spin_up, feedback_loop: bool = False):
    # load MODFLOW model - basic info and RCH package
    modflow_model = flopy.modflow.Modflow.load(nam_file, model_ws=modflow_path,
                                               load_only=["rch"],
                                               forgive=True)

    shapes_for_model = [np.load(local_paths.get_shape_path(project_id, shape_id))
                        for shape_id in assigned_shape_ids]

    if feedback_loop and isinstance(mapping_val, str):
        for shape_id, shape_mask in zip(assigned_shape_ids, shapes_for_model):
            sum_v_bot = __get_sum_vbot(mapping_val, project_id, spin_up, shape_id=shape_id)
            __recharge_update(modflow_model, shapes_for_model, sum_v_bot)
    else:
        sum_v_bot = __get_sum_vbot(mapping_val, project_id, spin_up)
        __recharge_update(modflow_model, shapes_for_model, sum_v_bot)

    new_recharge = modflow_model.rch.rech
    rch_package = modflow_model.get_package("rch")  # get the RCH package
    # generate and save new RCH (same properties, different recharge)
    flopy.modflow.ModflowRch(modflow_model, nrchop=rch_package.nrchop, ipakcb=rch_package.ipakcb,
                             rech=new_recharge,
                             irch=rch_package.irch).write_file(check=False)


def __get_sum_vbot(mapping_val, project_id, spin_up, shape_id: Optional[str] = None):
    if isinstance(mapping_val, str):
        hydrus_model_dir = local_paths.get_hydrus_model_path(project_id,
                                                             hydrus_id=mapping_val,
                                                             simulation_mode=True,
                                                             shape_id=shape_id)
        hydrus_recharge_path = os.path.join(hydrus_model_dir, 'T_Level.out')
        sum_v_bot = ph.read.read_tlevel(path=hydrus_recharge_path)['sum(vBot)']

        # calc difference for each day (excluding spin_up period)
        if spin_up >= len(sum_v_bot):
            raise DataProcessingException('Spin up is longer than hydrus model time')

        sum_vbot_val = sum_v_bot.iloc[-1]
        if spin_up > 0:
            sum_vbot_val -= sum_v_bot.iloc[spin_up - 1]

        return sum_vbot_val / (len(sum_v_bot) - spin_up)  # (-np.diff(sum_v_bot))[spin_up:]
    elif isinstance(mapping_val, float):
        return mapping_val
    else:
        raise DataProcessingException("Unknown mapping in simulation!")


def __recharge_update(modflow_model, shapes_for_model, avg_sum_v_bot):
    shape = max(shapes_for_model) if len(shapes_for_model) > 1 else shapes_for_model[0]
    mask = (shape == 1)  # Frontend sets explicitly 1
    for idx, stress_period_duration in enumerate(modflow_model.modeltime.perlen):
        # modflow rch array for given stress period
        recharge_modflow_array = modflow_model.rch.rech[idx].array

        # add calculated hydrus average sum(vBot) to modflow recharge array
        recharge_modflow_array[mask] = avg_sum_v_bot

        # save calculated recharge to modflow model
        modflow_model.rch.rech[idx] = recharge_modflow_array


def transfer_water_level_to_hydrus(project_id: str,
                                   hydrus_id: str,
                                   modflow_id: str,
                                   shape_id: str,
                                   use_modflow_results: bool = True) -> None:
    compound_hydrus_id = get_feedback_loop_hydrus_name(hydrus_id, shape_id)
    water_avg_depth = modflow_model_management.get_avg_water_depth_for_shape(project_id=project_id,
                                                                             modflow_id=modflow_id,
                                                                             shape_id=shape_id,
                                                                             use_modflow_results=use_modflow_results)
    hydrus_profile_depth = hydrus_model_management.get_profile_depth(project_id, hydrus_id=compound_hydrus_id)
    btm_pressure = hydrus_profile_depth - water_avg_depth
    hydrus_model_management.update_bottom_pressure(project_id=project_id,
                                                   hydrus_id=compound_hydrus_id,
                                                   btm_pressure_val=btm_pressure)


def pass_weather_data_to_hydrus(project_id: str,
                                hydrus_to_weather_mapping: Dict[str, str]) -> None:
    for hydrus_id, weather_id in hydrus_to_weather_mapping:
        hydrus_path = local_paths.get_hydrus_model_path(project_id, hydrus_id, simulation_mode=True)
        hydrus_length_unit = hydrus_utils.get_hydrus_length_unit(hydrus_path)
        raw_data = weather_util.read_weather_csv(local_paths.get_weather_model_path(project_id, weather_id))
        ready_data = weather_util.adapt_data(raw_data, hydrus_length_unit)
        success = weather_util.add_weather_to_hydrus_model(hydrus_path, ready_data)
        if not success:
            raise DataProcessingException(f"Error occurred during applying "
                                          f"weather file {weather_id} to hydrus model {hydrus_id}")
