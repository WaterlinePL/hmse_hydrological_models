import glob
import os.path

import numpy as np
import phydrus as ph
from matplotlib import pyplot as plt

from ...hydrus import hydrus_utils


def create_recharge_plot(project_local_path: str, combined: bool):
    plot_data = []
    t_counter = 0

    first_run = True
    labels = []

    for step_dir in sorted(glob.glob(os.path.join(project_local_path, "simulation", "sim_step_*")), key=len):
        step_data = []
        for hydrus_model in glob.glob(os.path.join(step_dir, "hydrus/*")):
            t_level_path = hydrus_utils.find_hydrus_file_path(hydrus_model, "t_level.out")
            # step_data.append(ph.read.read_tlevel(path=t_level_path)["vBot"].values)
            step_data.append([ph.read.read_tlevel(path=t_level_path)["sum(vBot)"].iloc[-1]])
            if first_run:
                if combined:
                    labels.append("total recharge")
                    first_run = False
                else:
                    labels.append(os.path.basename(hydrus_model))

        first_run = False

        if len(step_data) == 0:
            continue
        t_vals = np.arange(t_counter, t_counter + len(step_data[0]))

        if combined:
            step_plot_data = np.column_stack([t_vals, np.array(step_data).sum(axis=0)])
        else:
            step_plot_data = np.column_stack([t_vals] + [*step_data])

        if len(plot_data) == 0:
            plot_data = step_plot_data.copy()
        else:
            plot_data = np.append(plot_data, step_plot_data, axis=0)

        if len(step_data) > 0:
            t_counter += len(step_data[0])

    plt.title("Recharge in Hydrus")
    plt.xlabel("Time [d]")
    plt.ylabel("Recharge [m/d]")

    colors = ["blue", "red", "green"]

    for i in range(1, plot_data.shape[1]):
        plt.plot(plot_data[:, 0], plot_data[:, i], colors[i])

    plt.legend(labels)
    plt.show()
