"""
This script is the second part of mujoco_gernerate_data and append the info file with regression data.
User can choose :
- the type of algorithm : Sindy, XLSindy
- the regression algorithm : coordinate descent (scipy lasso), hard treshold
- level of noise added to imported data
"""

# tyro cly dependencies
from dataclasses import dataclass
from dataclasses import field
from typing import List
import tyro

import xlsindy

import numpy as np
import json

import sys
import os
import importlib

from jax import jit
from jax import vmap

import pandas as pd

import matplotlib.pyplot as plt


@dataclass
class Args:
    experiment_file: str = "None"
    """the experiment file (without extension)"""
    optimization_function: str = "lasso_regression"
    """the regression function used in the regression"""
    algorithm: str = "xlsindy"
    """the name of the algorithm used (for the moment "xlsindy" and "sindy" are the only possible)"""
    noise_level: float = 0.0
    """the level of noise introduce in the experiment"""
    random_seed: List[int] = field(default_factory=lambda: [0])
    """the random seed for the noise"""
    validation_on_database: bool = True
    """if true validate the model on the database file"""


if __name__ == "__main__":

    args = tyro.cli(Args)

    ## CLI validation
    if args.experiment_file == "None":
        raise ValueError(
            "experiment_file should be provided, don't hesitate to invoke --help"
        )

    with open(args.experiment_file + ".json", "r") as json_file:
        simulation_dict = json.load(json_file)

    folder_path = os.path.join(
        os.path.dirname(__file__),
        "mujoco_align_data/" + simulation_dict["input"]["experiment_folder"],
    )
    sys.path.append(folder_path)

    # import the xlsindy_gen.py script
    xlsindy_gen = importlib.import_module("xlsindy_gen")

    try:
        xlsindy_component = eval(f"xlsindy_gen.xlsindy_component")
    except AttributeError:
        raise AttributeError(
            f"xlsindy_gen.py should contain a function named {args.algorithm}_component in order to work with algorithm {args.algorithm}"
        )

    try:
        forces_wrapper = xlsindy_gen.forces_wrapper
    except AttributeError:
        forces_wrapper = None

    num_coordinates, time_sym, symbols_matrix, catalog_repartition, extra_info = (
        xlsindy_component(mode=args.algorithm, random_seed=args.random_seed)
    )

    regression_function = eval(f"xlsindy.optimization.{args.optimization_function}")

    sim_data = np.load(args.experiment_file + ".npz")

    rng = np.random.default_rng(args.random_seed)

    # load
    imported_time = sim_data["array1"]
    imported_qpos = sim_data["array2"]
    imported_qvel = sim_data["array3"]
    imported_qacc = sim_data["array4"]
    imported_force = sim_data["array5"]

    # debug
    print(
        "debug mujoco :",
        len(imported_time),
        np.sum(imported_qpos),
        np.sum(imported_qvel),
        np.sum(imported_qacc),
        np.sum(imported_force),
    )
    # add noise
    imported_qpos += rng.normal(loc=0, scale=args.noise_level, size=imported_qpos.shape)
    imported_qvel += rng.normal(loc=0, scale=args.noise_level, size=imported_qvel.shape)
    imported_qacc += rng.normal(loc=0, scale=args.noise_level, size=imported_qacc.shape)
    imported_force += rng.normal(
        loc=0, scale=args.noise_level, size=imported_force.shape
    )

    fig, axs = plt.subplots(4, 1, sharex=True, figsize=(10, 8))

    # Plot each time series
    axs[0].plot(imported_time, imported_qpos, label="qpos", color="tab:blue")
    axs[0].set_ylabel("qpos")
    axs[0].legend(loc="upper right")

    axs[1].plot(imported_time, imported_qvel, label="qvel", color="tab:orange")
    axs[1].set_ylabel("qvel")
    axs[1].legend(loc="upper right")

    axs[2].plot(imported_time, imported_qacc, label="qacc", color="tab:green")
    axs[2].set_ylabel("qacc")
    axs[2].legend(loc="upper right")

    axs[3].plot(imported_time, imported_force, label="force", color="tab:red")
    axs[3].set_ylabel("force")
    axs[3].set_xlabel("Time")
    axs[3].legend(loc="upper right")

    plt.tight_layout()
    plt.show()
