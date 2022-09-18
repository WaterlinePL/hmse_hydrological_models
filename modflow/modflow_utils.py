import os
import tempfile
from collections import deque
from typing import List, Tuple, Optional
from zipfile import ZipFile

import flopy
import numpy as np

from hmse_simulations.hmse_projects.hmse_hydrological_models.model_exceptions import ModflowMissingFileError, \
    ModflowCommonError
from hmse_simulations.hmse_projects.hmse_hydrological_models.modflow.modflow_metadata import ModflowMetadata


def adapt_model_to_display(metadata: ModflowMetadata):
    row_cells, col_cells = scale_cells_size(metadata.row_cells, metadata.col_cells)
    return ModflowMetadata(modflow_id=metadata.modflow_id,
                           rows=metadata.rows, cols=metadata.cols,
                           row_cells=row_cells, col_cells=col_cells,
                           grid_unit=metadata.grid_unit)


def extract_metadata(modflow_archive, tmp_dir: os.PathLike) -> Tuple[ModflowMetadata, List[np.ndarray]]:
    extension = modflow_archive.filename.split('.')[-1]
    modflow_id = modflow_archive.filename.replace(f".{extension}", "")

    modflow_path = os.path.join(tmp_dir, modflow_archive.filename)
    modflow_archive.save(modflow_path)
    with ZipFile(modflow_path, 'r') as archive:
        archive.extractall(tmp_dir)
        __validate_model(tmp_dir)

        model = flopy.modflow.Modflow.load(scan_for_modflow_file(tmp_dir),
                                           model_ws=tmp_dir,
                                           load_only=["rch", "dis"],
                                           forgive=True)

        model_shape = (model.nrow, model.ncol)
        model_metadata = ModflowMetadata(modflow_id,
                                         rows=model_shape[0], cols=model_shape[1],
                                         row_cells=model.dis.delc.array.tolist(),
                                         col_cells=model.dis.delr.array.tolist(),
                                         grid_unit=model.modelgrid.units)
        return model_metadata, get_shapes_from_rch(model_path=tmp_dir, model_shape=model_shape)


def __validate_model(model_path: os.PathLike) -> None:
    """
    Validates modflow model - check if it contains .nam file (list of files), .rch file (recharge),
    perform recharge check.

    @param model_path: Path to Modflow project main directory
    @return: True if model is valid, False otherwise
    """

    nam_file_name = scan_for_modflow_file(model_path)
    if not nam_file_name:
        raise ModflowMissingFileError(description="Invalid Modflow model - .nam file not found!")

    try:
        # load whole model and validate it
        m = flopy.modflow.Modflow.load(nam_file_name,
                                       model_ws=model_path,
                                       forgive=True,
                                       check=True)
        if m.rch is None:
            raise ModflowMissingFileError(description="Invalid Modflow model - .rch file not found!")
        m.rch.check()
    except IOError:
        raise ModflowMissingFileError(description="Invalid Modflow model - validation detected missing files!")
    except KeyError:
        raise ModflowCommonError(description="Invalid Modflow model - validation detected an unspecified error!")


def scale_cells_size(row_cells: List[float],
                     col_cells: List[float],
                     max_width: float = 500) -> Tuple[List[float], List[float]]:
    """
    Get cells size of modflow model
    @param col_cells: list of modflow model cols width
    @param row_cells: list of modflow model rows height
    @param max_width: Parameter for scaling purposes
    @return: Tuple with lists containing width of the Modflow project cells (row_cells, col_cells)
    """

    sum_width = sum(col_cells)
    sum_height = sum(row_cells)

    width = max_width
    height = max_width * (sum_height / sum_width)

    scale_x = sum_width / width
    scale_y = sum_height / height

    row_cells /= scale_x
    col_cells /= scale_y

    return row_cells, col_cells


def get_shapes_from_rch(model_path: os.PathLike, model_shape: Tuple[int, int]) -> List[np.ndarray]:
    """
    Defines shapes masks for uploaded Modflow model based on recharge

    @param model_path: Path of Modflow model
    @param model_shape: Tuple representing size of the Modflow project (rows, cols)
    @return: List of shapes read from Modflow project
    """

    nam_file_name = scan_for_modflow_file(model_path)
    modflow_model = flopy.modflow.Modflow.load(nam_file_name,
                                               model_ws=model_path,
                                               load_only=["rch"],
                                               forgive=True)

    # FIXME: This MIGHT require a consultation with somebody
    stress_period = 0
    layer = 0

    recharge_masks = []
    is_checked_array = np.full(model_shape, False)
    recharge_array = modflow_model.rch.rech.array[stress_period][layer]
    modflow_rows, modflow_cols = model_shape

    for row in range(modflow_rows):
        for col in range(modflow_cols):
            if not is_checked_array[row][col]:
                recharge_masks.append(np.zeros(model_shape))
                __fill_mask_iterative(mask=recharge_masks[-1], recharge_array=recharge_array,
                                      is_checked_array=is_checked_array,
                                      project_shape=model_shape,
                                      row=row, col=col,
                                      value=recharge_array[row][col])

    return recharge_masks


def __fill_mask_iterative(mask: np.ndarray,
                          recharge_array: np.ndarray,
                          is_checked_array: np.ndarray,
                          project_shape: Tuple[int, int],
                          row: int,
                          col: int,
                          value: float):
    """
    Fill given mask with 1's according to recharge array (using DFS)

    @param mask: Binary mask of current shape - initially filled with 0's
    @param recharge_array: 2d array filled with modflow model recharge values
    @param is_checked_array: Control array - 'True' means that given cell was already used in one of the masks
    @param project_shape: Tuple representing shape of the Modflow project (rows, cols)
    @param row: Current column index
    @param col: Current row index
    @param value: Recharge value of current mask
    @return: None (result inside variable @mask)
    """
    modflow_rows, modflow_cols = project_shape

    stack = deque()
    stack.append((row, col))

    while stack:
        cur_row, cur_col = stack.pop()
        # return condition - out of bounds or given cell was already used
        if cur_row < 0 or cur_row >= modflow_rows or cur_col < 0 or cur_col >= modflow_cols or \
                is_checked_array[cur_row][cur_col]:
            continue

        if recharge_array[cur_row][cur_col] == value:
            is_checked_array[cur_row][cur_col] = True
            mask[cur_row][cur_col] = 1
            stack.append((cur_row - 1, cur_col))
            stack.append((cur_row + 1, cur_col))
            stack.append((cur_row, cur_col - 1))
            stack.append((cur_row, cur_col + 1))


def scan_for_modflow_file(model_path: os.PathLike, ext: str = ".nam") -> Optional[str]:
    for file in os.listdir(model_path):
        if file.endswith(ext):
            return file
    return None
