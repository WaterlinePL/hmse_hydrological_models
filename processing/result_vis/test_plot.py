# from .project_plotter import plot_project
from hmse_simulations.hmse_projects.hmse_hydrological_models.processing.result_vis.project_plotter import plot_project

if __name__ == "__main__":
    proj_path = "feedback-test"
    plot_project(proj_path)
