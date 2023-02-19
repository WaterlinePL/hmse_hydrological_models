import os
from typing import Dict, Union, List

import flopy
import numpy as np
import phydrus as ph

from .hydrus import hydrus_utils
from .local_fs_configuration import local_paths
from .modflow import modflow_utils
from .weather_data import weather_util


class DataProcessingException(RuntimeError):
    pass


def recharge_from_hydrus_to_modflow(project_id: str,
                                    modflow_id: str,
                                    spin_up: int,
                                    model_to_shapes_mapping: Dict[Union[str, float], List[str]]) -> None:
    """
    @param model_to_shapes_mapping: Hydrus model/float value -> list of shape_id assigned to that shape
    """
    modflow_path = local_paths.get_modflow_model_path(project_id, modflow_id, simulation_mode=True)
    nam_file = modflow_utils.scan_for_modflow_file(modflow_path)

    for mapping_val, assigned_shape_ids in model_to_shapes_mapping:
        shapes_for_model = [np.load(local_paths.get_shape_path(project_id, shape_id))
                            for shape_id in assigned_shape_ids]
        # load MODFLOW model - basic info and RCH package
        modflow_model = flopy.modflow.Modflow.load(nam_file, model_ws=modflow_path,
                                                   load_only=["rch"],
                                                   forgive=True)
        if isinstance(mapping_val, str):
            hydrus_model_dir = local_paths.get_hydrus_model_path(project_id,
                                                                 hydrus_id=mapping_val,
                                                                 simulation_mode=True)
            hydrus_recharge_path = os.path.join(hydrus_model_dir, 'T_Level.out')
            sum_v_bot = ph.read.read_tlevel(path=hydrus_recharge_path)['sum(vBot)']

            # calc difference for each day (excluding spin_up period)
            sum_v_bot = (-np.diff(sum_v_bot))[spin_up:]
            if spin_up >= len(sum_v_bot):
                raise DataProcessingException('Spin up is longer than hydrus model time')

        elif isinstance(mapping_val, float):
            sum_v_bot = mapping_val

        else:
            raise DataProcessingException("Unknown mapping in simulation!")

        for shape in shapes_for_model:
            mask = (shape == 1)  # Frontend sets explicitly 1

            stress_period_begin = 0  # beginning of current stress period
            for idx, stress_period_duration in enumerate(modflow_model.modeltime.perlen):
                # float -> int indexing purposes
                stress_period_duration = int(stress_period_duration)

                # modflow rch array for given stress period
                recharge_modflow_array = modflow_model.rch.rech[idx].array

                if isinstance(sum_v_bot, float):
                    avg_v_bot_stress_period = sum_v_bot
                else:
                    # average from all hydrus sum(vBot) values during given stress period
                    stress_period_end = stress_period_begin + stress_period_duration
                    if stress_period_begin >= len(sum_v_bot) or stress_period_end >= len(sum_v_bot):
                        raise DataProcessingException(f"Stress period {idx + 1} exceeds hydrus model time")
                    avg_v_bot_stress_period = np.average(sum_v_bot[stress_period_begin:stress_period_end])

                # add calculated hydrus average sum(vBot) to modflow recharge array
                recharge_modflow_array[mask] = avg_v_bot_stress_period

                # save calculated recharge to modflow model
                modflow_model.rch.rech[idx] = recharge_modflow_array

                # update beginning of current stress period
                stress_period_begin += stress_period_duration

        new_recharge = modflow_model.rch.rech
        rch_package = modflow_model.get_package("rch")  # get the RCH package

        # generate and save new RCH (same properties, different recharge)
        flopy.modflow.ModflowRch(modflow_model, nrchop=rch_package.nrchop, ipakcb=rch_package.ipakcb,
                                 rech=new_recharge,
                                 irch=rch_package.irch).write_file(check=False)


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
