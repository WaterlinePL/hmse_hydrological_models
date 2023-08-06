import json
from argparse import ArgumentParser
from json import JSONDecodeError
from typing import Dict

from processing.modflow.modflow_metadata import ModflowMetadata
# very important imports - used in CLI, accessed through globals() dict
from processing.task_logic.data_tasks_logic import \
    weather_data_transfer_to_hydrus, transfer_data_from_hydrus_to_modflow, transfer_data_from_modflow_to_hydrus, \
    transfer_data_from_modflow_to_hydrus_init_transient
from processing.unit_manager import LengthUnit
from processing.task_logic.configuration_tasks_logic import local_files_initialization, extract_output_to_json, \
    initialize_feedback_iteration, create_hydrus_models_for_zones, pre_configure_iteration, cleanup_project_volume, \
    preserve_reference_hydrus_models


def __create_parser() -> ArgumentParser:
    arg_parser = ArgumentParser(prog="HMSE hydrological models CLI",
                                description="Command line interface for manipulating projects",
                                )
    arg_parser.add_argument("--action",
                            choices=[
                                "local_files_initialization",
                                "extract_output_to_json",
                                "initialize_feedback_iteration",
                                "preserve_reference_hydrus_models",
                                "create_hydrus_models_for_zones",
                                "pre_configure_iteration",
                                "cleanup_project_volume",
                                "weather_data_transfer_to_hydrus",
                                "transfer_data_from_hydrus_to_modflow",
                                "transfer_data_from_modflow_to_hydrus",
                                "transfer_data_from_modflow_to_hydrus_init_transient"
                            ],
                            nargs="+",
                            required=True)  # name of function to call as str
    arg_parser.add_argument("--project_id", required=True)
    arg_parser.add_argument("--start_date")  # str
    arg_parser.add_argument("--modflow_metadata")   # JSON string with dict
    arg_parser.add_argument("--shapes_to_hydrus")   # JSON string with dict
    arg_parser.add_argument("--hydrus_to_weather")  # JSON string with dict
    arg_parser.add_argument("--is_feedback_loop", action="store_true")
    arg_parser.add_argument("--no_feedback_loop", action="store_false", dest="is_feedback_loop")
    arg_parser.add_argument("--spin_up", type=int)
    return arg_parser


def __parse_cli_kwargs(project_kwargs: Dict):
    # Only needed params filled in
    try:
        project_kwargs["modflow_metadata"] = ModflowMetadata(**(json.loads(project_kwargs["modflow_metadata"])))
    except:
        pass
    try:
        project_kwargs["shapes_to_hydrus"] = json.loads(project_kwargs["shapes_to_hydrus"])
    except:
        pass
    try:
        project_kwargs["hydrus_to_weather"] = json.loads(project_kwargs["hydrus_to_weather"])
    except:
        pass
    return project_kwargs


if __name__ == "__main__":
    parser = __create_parser()
    cli_kwargs = parser.parse_args().__dict__
    function_names = cli_kwargs.pop("action")
    parsed_kwargs = __parse_cli_kwargs(cli_kwargs)
    for func_name in function_names:
        function_to_call = globals()[func_name]
        function_to_call(**parsed_kwargs)
