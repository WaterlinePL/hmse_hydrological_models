WORKSPACE_PATH = 'workspace'
SIMULATION_DIR = "simulation"

METADATA_FILENAME = 'metadata.json'
MODFLOW_OUTPUT_JSON = "results.json"


def get_feedback_loop_hydrus_name(hydrus_id: str, shape_id: str) -> str:
    return f"{hydrus_id}--{shape_id}"
