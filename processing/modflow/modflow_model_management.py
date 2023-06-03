import os
import shutil
from typing import Optional

import flopy
import numpy as np
from flopy.modflow import Modflow, ModflowBas
from flopy.utils import FormattedHeadFile

from . import modflow_package_manager
from ..local_fs_configuration import local_paths
from ..local_fs_configuration.feedback_loop_file_management import find_previous_simulation_step_dir
from ..modflow import modflow_utils


def prepare_model_for_next_iteration(project_id: str, modflow_id: str) -> None:
    prev_sim_step_dir = find_previous_simulation_step_dir(project_id)
    prev_modflow_dir = os.path.join(prev_sim_step_dir, 'modflow', modflow_id) if prev_sim_step_dir else None
    next_modflow_dir = local_paths.get_modflow_model_path(project_id, modflow_id, simulation_mode=True)
    ref_modflow_dir = local_paths.get_modflow_model_path(project_id, modflow_id, simulation_mode=False)
    step = 0 if not prev_sim_step_dir else int(prev_sim_step_dir.split('_')[-1]) + 1
    __create_temporary_model(ref_modflow_dir, prev_modflow_dir, next_modflow_dir, step)


def get_avg_water_depth_for_shape(project_id: str,
                                  modflow_id: str,
                                  shape_id: str,
                                  use_modflow_results: bool) -> float:
    model_dir = local_paths.get_modflow_model_path(project_id, modflow_id, simulation_mode=True)
    nam_file_name = modflow_utils.scan_for_modflow_file(model_dir, ext=".nam")

    packages = ["dis", "bas6"]
    if use_modflow_results:
        fhd_file_name = modflow_utils.scan_for_modflow_file(model_dir, ext=".fhd")
        fhd_data = FormattedHeadFile(os.path.join(model_dir, fhd_file_name))
    else:
        fhd_data = None

    model = Modflow.load(nam_file_name, model_ws=model_dir, load_only=packages, forgive=True)
    mask = np.load(local_paths.get_shape_path(project_id, shape_id))
    avg_terrain_lvl = __get_avg_terrain_level(model, shape_mask=mask)

    inbound = next(pkg for pkg in model.packagelist if isinstance(pkg, ModflowBas)).ibound[0].array
    avg_water_lvl = __get_avg_water_level(model, shape_mask=mask*inbound, fhd_data=fhd_data)

    if use_modflow_results:
        fhd_data.close()
    return avg_terrain_lvl - avg_water_lvl


def __get_avg_terrain_level(model: Modflow, shape_mask: np.ndarray) -> float:
    return float(np.average(model.modelgrid.top[shape_mask == 1]))


def __get_avg_water_level(model: Modflow, shape_mask: np.ndarray,
                          fhd_data: Optional[FormattedHeadFile] = None) -> float:
    if fhd_data:
        water_lvl_array = fhd_data.get_data()[0]
    else:
        bas_package = next(pkg for pkg in model.packagelist if isinstance(pkg, ModflowBas))
        water_lvl_array = bas_package.strt[0].array
    return float(np.average(water_lvl_array[shape_mask == 1]))


def __create_temporary_model(ref_modflow_dir: str, prev_modflow_dir: Optional[str], new_modflow_dir: str, step: int):
    shutil.rmtree(new_modflow_dir, ignore_errors=True)
    shutil.copytree(ref_modflow_dir, new_modflow_dir)
    dst_model = flopy.modflow.Modflow.load(modflow_utils.scan_for_modflow_file(new_modflow_dir, ext=".nam"),
                                           model_ws=new_modflow_dir,
                                           forgive=True)

    # Initial conditions from previous iteration
    if prev_modflow_dir is not None:
        prev_model_fhd_path = os.path.join(prev_modflow_dir, modflow_utils.scan_for_modflow_file(prev_modflow_dir,
                                                                                                 ext=".fhd"))
        prev_model_fhd = FormattedHeadFile(prev_model_fhd_path)
        bas_package = next(pkg for pkg in dst_model.packagelist if isinstance(pkg, ModflowBas))
        bas_package.strt = prev_model_fhd.get_data()
        bas_package.write_file()
        prev_model_fhd.close()

    # Crop packages to one timestep
    modflow_package_manager.create_packages_for_step(dst_model, step)
