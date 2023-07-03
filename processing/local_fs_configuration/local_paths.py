import os
from typing import Optional

from .path_constants import WORKSPACE_PATH, SIMULATION_DIR, METADATA_FILENAME, MODFLOW_OUTPUT_JSON,\
    get_feedback_loop_hydrus_name


def get_root_dir(project_id: str, simulation_mode: bool) -> str:
    return get_simulation_dir(project_id) if simulation_mode else get_project_dir(project_id)


def get_simulation_dir(project_id: str) -> str:
    return os.path.join(get_project_dir(project_id), SIMULATION_DIR)


def get_project_dir(project_id: str) -> str:
    return os.path.join(WORKSPACE_PATH, project_id)


def get_project_metadata_path(project_id: str) -> str:
    return os.path.join(WORKSPACE_PATH, project_id, METADATA_FILENAME)


def get_modflow_dir(project_id: str, simulation_mode: bool = False, simulation_ref: bool = False) -> str:
    if simulation_ref:
        assert simulation_mode
        return os.path.join(get_root_dir(project_id, simulation_mode), "ref", "modflow")
    return os.path.join(get_root_dir(project_id, simulation_mode), "modflow")


def get_hydrus_dir(project_id: str, simulation_mode: bool = False, simulation_ref: bool = False) -> str:
    if simulation_ref:
        assert simulation_mode
        return os.path.join(get_root_dir(project_id, simulation_mode), "ref", "hydrus")
    return os.path.join(get_root_dir(project_id, simulation_mode), "hydrus")


def get_weather_dir(project_id: str, simulation_mode: bool = False) -> str:
    return os.path.join(get_root_dir(project_id, simulation_mode), "weather")


def get_shapes_dir(project_id: str, simulation_mode: bool = False) -> str:
    return os.path.join(get_root_dir(project_id, simulation_mode), "shapes")


def get_rch_shapes_dir(project_id: str, simulation_mode: bool = False) -> str:
    return os.path.join(get_root_dir(project_id, simulation_mode), "rch_shapes")


def get_modflow_model_path(project_id: str, modflow_id: str,
                           simulation_mode: bool = False, simulation_ref: bool = False) -> str:
    return os.path.join(get_modflow_dir(project_id, simulation_mode, simulation_ref), modflow_id)


def get_hydrus_model_path(project_id: str, hydrus_id: str,
                          simulation_mode: bool = False, simulation_ref: bool = False,
                          shape_id: Optional[str] = None) -> str:
    true_hydrus_id = get_feedback_loop_hydrus_name(hydrus_id, shape_id) if shape_id else hydrus_id
    return os.path.join(get_hydrus_dir(project_id, simulation_mode, simulation_ref), true_hydrus_id)


def get_simulation_per_shape_hydrus_model_path(project_id: str, hydrus_id: str, shape_id: str) -> str:
    return os.path.join(get_hydrus_dir(project_id, simulation_mode=True),
                        get_feedback_loop_hydrus_name(hydrus_id, shape_id))


def get_weather_model_path(project_id: str, weather_id: str, simulation_mode: bool = False) -> str:
    return os.path.join(get_weather_dir(project_id, simulation_mode), f"{weather_id}.csv")


def get_shape_path(project_id: str, shape_id: str, simulation_mode: bool = False) -> str:
    return os.path.join(get_shapes_dir(project_id, simulation_mode), f"{shape_id}.npy")


def get_rch_shape_filepath(project_id: str, shape_id: str, simulation_mode: bool = False) -> str:
    return os.path.join(get_rch_shapes_dir(project_id, simulation_mode), f"{shape_id}.npy")


def get_output_json_path(project_id: str) -> str:
    return os.path.join(get_simulation_dir(project_id), MODFLOW_OUTPUT_JSON)
