from typing import Dict, Union

from .. import data_passing_utils
from ..hydrus import hydrus_utils
from ..modflow.modflow_metadata import ModflowMetadata


def weather_data_transfer_to_hydrus(project_id: str, hydrus_to_weather: Dict[str, str],
                                    shapes_to_hydrus: Dict[str, Union[str, float]], **kwargs):
    hydrus_to_weather_mapping = {hydrus_id: hydrus_to_weather[hydrus_id]
                                 for hydrus_id in hydrus_utils.get_used_hydrus_models(shapes_to_hydrus)
                                 if hydrus_id in hydrus_to_weather}

    data_passing_utils.pass_weather_data_to_hydrus(
        project_id=project_id,
        hydrus_to_weather_mapping=hydrus_to_weather_mapping
    )


def transfer_data_from_hydrus_to_modflow(project_id: str, shapes_to_hydrus: Dict[str, Union[str, float]],
                                         is_feedback_loop: bool, modflow_metadata: ModflowMetadata, spin_up: int,
                                         **kwargs):
    model_to_shapes_mapping = hydrus_utils.get_hydrus_mapping_for_transfer_to_modflow(
        shapes_to_hydrus,
        use_compound_hydrus_ids=is_feedback_loop
    )
    data_passing_utils.recharge_from_hydrus_to_modflow(
        project_id=project_id,
        modflow_metadata=modflow_metadata,
        spin_up=spin_up,
        model_to_shapes_mapping=model_to_shapes_mapping,
        feedback_loop=is_feedback_loop
    )


def transfer_data_from_modflow_to_hydrus(project_id: str,
                                         shapes_to_hydrus: Dict[str, Union[str, float]],
                                         modflow_metadata: ModflowMetadata,
                                         **kwargs):
    __transfer_from_modflow_to_hydrus(
        project_id=project_id,
        shapes_to_hydrus=shapes_to_hydrus,
        modflow_metadata=modflow_metadata,
        use_modflow_results=True
    )


def transfer_data_from_modflow_to_hydrus_init_transient(project_id: str,
                                                        shapes_to_hydrus: Dict[str, Union[str, float]],
                                                        modflow_metadata: ModflowMetadata,
                                                        **kwargs):
    __transfer_from_modflow_to_hydrus(
        project_id=project_id,
        shapes_to_hydrus=shapes_to_hydrus,
        modflow_metadata=modflow_metadata,
        use_modflow_results=False
    )


def __transfer_from_modflow_to_hydrus(project_id: str,
                                      shapes_to_hydrus: Dict[str, Union[str, float]],
                                      modflow_metadata: ModflowMetadata,
                                      use_modflow_results: bool):
    for shape_id, plain_hydrus_id in shapes_to_hydrus.items():
        if not isinstance(plain_hydrus_id, str):
            continue
        data_passing_utils.transfer_water_level_to_hydrus(project_id,
                                                          plain_hydrus_id,
                                                          modflow_metadata,
                                                          shape_id,
                                                          use_modflow_results)
