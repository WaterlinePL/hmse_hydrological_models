import glob
import os

import numpy as np
from flopy.modflow import Modflow, ModflowBas
from flopy.utils import FormattedHeadFile
from matplotlib import pyplot as plt

from hmse_simulations.hmse_projects.hmse_hydrological_models.processing.modflow import modflow_utils


def create_water_level_plot(project_local_path: str):
    plot_data = []
    t_counter = 0

    shapes_for_zones = {}
    for np_shape_path in glob.glob(os.path.join(project_local_path, "simulation", "shapes/*")):
        shape_name = os.path.basename(np_shape_path)
        shapes_for_zones[shape_name] = np.load(np_shape_path)

    first_run = True
    labels = []

    for step_dir in sorted(glob.glob(os.path.join(project_local_path, "simulation", "sim_step_*")), key=len):
        step_data = []
        mf_model_path = glob.glob(os.path.join(step_dir, "modflow/*"))[0]
        fhd_path = os.path.join(mf_model_path, modflow_utils.scan_for_modflow_file(mf_model_path, ext=".fhd"))
        fhd_data = FormattedHeadFile(fhd_path).get_data()
        model = Modflow.load(modflow_utils.scan_for_modflow_file(mf_model_path, ext=".nam"),
                             model_ws=mf_model_path, load_only=["dis", "bas6"], forgive=True)
        inbound = next(pkg for pkg in model.packagelist if isinstance(pkg, ModflowBas)).ibound[0].array

        # TODO: load FHD
        #  mask and avg on that?
        for shape_name, shape_mask in shapes_for_zones.items():
            avg_val_in_shape = np.average(inbound * shape_mask * fhd_data)
            step_data.append(np.array([avg_val_in_shape]))
            if first_run:
                labels.append(os.path.basename(shape_name))

        first_run = False

        if len(step_data) == 0:
            continue
        t_vals = np.arange(t_counter, t_counter + len(step_data[0]))

        step_plot_data = np.column_stack([t_vals, *step_data])

        if len(plot_data) == 0:
            plot_data = step_plot_data.copy()
        else:
            plot_data = np.append(plot_data, step_plot_data, axis=0)

        if len(step_data) > 0:
            t_counter += len(step_data[0])

    plt.title("Water level in Modflow")
    plt.xlabel("Time [d]")
    plt.ylabel("Water level TODO: unit")

    colors = ["blue", "red", "green"]

    for i in range(1, plot_data.shape[1]):
        plt.plot(plot_data[:, 0], plot_data[:, i], colors[i-1])

    plt.legend(labels)
    plt.show()
