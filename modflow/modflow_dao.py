from abc import ABC, abstractmethod

from hmse_hydrological_models.modflow.modflow_metadata import ModflowMetadata


class ModflowModelDao(ABC):

    @abstractmethod
    def get_model_data(self, modflow_model_id: str) -> ModflowMetadata:
        """
        Get Modflow model metadata

        @param modflow_model_id: Path to Modflow project main directory
        @return: Modflow project metadata.
        """
        ...

    @abstractmethod
    def get_model_data_from_project(self, project_id: str) -> ModflowMetadata:
        """
        Get Modflow model metadata

        @param project_id: ID of a particular project
        @return: Modflow project metadata.
        """
        ...


modflow_model_dao = ModflowModelDao()
