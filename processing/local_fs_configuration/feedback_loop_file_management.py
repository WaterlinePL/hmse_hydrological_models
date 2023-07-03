import os
import shutil
from typing import Dict, List, Optional

from ..local_fs_configuration import local_paths


def create_per_shape_hydrus_models(project_id: str, used_hydrus_models: Dict[str, List[str]]) -> None:
    hydrus_sim_dir = local_paths.get_hydrus_dir(project_id, simulation_mode=True)
    shutil.rmtree(hydrus_sim_dir)
    os.makedirs(hydrus_sim_dir, exist_ok=True)
    for hydrus_id in used_hydrus_models.keys():
        for shape_id in used_hydrus_models[hydrus_id]:
            ref_hydrus_path = local_paths.get_hydrus_model_path(project_id, hydrus_id,
                                                                simulation_mode=True,
                                                                simulation_ref=True)
            new_model_path = local_paths.get_hydrus_model_path(project_id, hydrus_id,
                                                               simulation_mode=True, shape_id=shape_id)
            shutil.copytree(ref_hydrus_path, new_model_path)


def pre_configure_iteration(project_id: str) -> None:
    prev_sim_step_dir = find_previous_simulation_step_dir(project_id)
    if not prev_sim_step_dir:
        step_dir_name = "sim_step_0"
    else:
        last_step = int(prev_sim_step_dir.split('_')[-1])
        step_dir_name = f"sim_step_{last_step + 1}"

    step_dir_path = os.path.join(local_paths.get_simulation_dir(project_id), step_dir_name)
    os.makedirs(step_dir_path)

    shutil.copytree(local_paths.get_modflow_dir(project_id, simulation_mode=True),
                    os.path.join(step_dir_path, "modflow"))
    shutil.copytree(local_paths.get_hydrus_dir(project_id, simulation_mode=True),
                    os.path.join(step_dir_path, "hydrus"))


def find_previous_simulation_step_dir(project_id: str) -> Optional[str]:
    step_nums = [int(file.split('_')[-1]) for file in os.listdir(local_paths.get_simulation_dir(project_id))
                 if file.startswith("sim_step_")]  # WARNING
    latest_step = sorted(step_nums, reverse=True)[0] if step_nums else None
    return (os.path.join(local_paths.get_simulation_dir(project_id), f"sim_step_{latest_step}")
            if latest_step is not None
            else None)
