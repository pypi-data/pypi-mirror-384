"""
This script attach the different exploration metric guess to info file of experiment
(override past metric computation)
This enable to make a linear regression on the different metric to get an experimentally guessed, exploration metric
"""

# tyro cly dependencies
from dataclasses import dataclass
from dataclasses import field
import tyro

import numpy as np
import json

import xlsindy


@dataclass
class Args:
    experiment_file: str = "None"
    """the experiment file"""


## list of metric function


def force_global_amplitude(
    imported_time, imported_qpos, imported_qvel, imported_qacc, imported_force
):

    return np.max(imported_force) - np.min(imported_force)


def log_force_global_amplitude(
    imported_time, imported_qpos, imported_qvel, imported_qacc, imported_force
):

    return np.log1p(np.max(imported_force) - np.min(imported_force))


def exploration_volumes(
    imported_time, imported_qpos, imported_qvel, imported_qacc, imported_force
):

    phase_portrait_explored = np.concatenate((imported_qpos, imported_qvel), axis=1)

    return xlsindy.result_formatting.estimate_volumes(
        phase_portrait_explored, 5
    )  # 5th nearest neighboor density estimation


def force_std(
    imported_time, imported_qpos, imported_qvel, imported_qacc, imported_force
):

    return np.std(imported_force)


def log_force_std(
    imported_time, imported_qpos, imported_qvel, imported_qacc, imported_force
):

    return np.log1p(np.std(imported_force))


def phase_std(
    imported_time, imported_qpos, imported_qvel, imported_qacc, imported_force
):

    phase_portrait_explored = np.concatenate((imported_qpos, imported_qvel), axis=1)

    return np.std(phase_portrait_explored)


def log_phase_std(
    imported_time, imported_qpos, imported_qvel, imported_qacc, imported_force
):

    phase_portrait_explored = np.concatenate((imported_qpos, imported_qvel), axis=1)

    return np.log1p(np.std(phase_portrait_explored))


metric_list = [
    force_global_amplitude,
    log_force_global_amplitude,
    exploration_volumes,
    log_force_std,
    force_std,
    phase_std,
    log_phase_std,
]

if __name__ == "__main__":

    args = tyro.cli(Args)

    with open(args.experiment_file + ".json", "r") as json_file:
        simulation_dict = json.load(json_file)

    sim_data = np.load(args.experiment_file + ".npz")
    imported_time = sim_data["array1"]
    imported_qpos = sim_data["array2"]
    imported_qvel = sim_data["array3"]
    imported_qacc = sim_data["array4"]
    imported_force = sim_data["array5"]

    simulation_dict["metric"] = {}

    for function in metric_list:

        simulation_dict["metric"][function.__name__] = function(
            imported_time, imported_qpos, imported_qvel, imported_qacc, imported_force
        )

    simulation_dict = xlsindy.result_formatting.convert_to_strings(simulation_dict)

    with open(args.experiment_file + ".json", "w") as file:
        json.dump(simulation_dict, file, indent=4)
