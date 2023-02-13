import os

from hmse_simulations.hmse_projects.hmse_hydrological_models.local_fs_configuration.path_constants import \
    WORKSPACE_PATH, SIMULATION_DIR


def get_simulation_dir(project_id: str):
    return os.path.join(WORKSPACE_PATH, project_id, SIMULATION_DIR)
