from .plots.recharge_plot import create_recharge_plot
from .plots.water_level_plot import create_water_level_plot


def plot_project(project_local_path: str):
    create_recharge_plot(project_local_path, combined=False)
    create_recharge_plot(project_local_path, combined=True)
    create_water_level_plot(project_local_path)
