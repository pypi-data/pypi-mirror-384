"""
This script is the second part of mujoco_gernerate_data and append the info file with regression data.
User can choose :
- the type of algorithm : Sindy, XLSindy
- the regression algorithm : coordinate descent (scipy lasso), hard treshold
- level of noise added to imported data

Actually align_data.py is in developpement, Implicit explicit regression is under test

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
    skip_already_done: bool = True
    """if true, skip the experiment if already present in the result file"""
    validation_on_database: bool = False
    """if true validate the model on the database file"""
    biparted_graph: bool = False
    """if true, plot the biparted graph in a svg file"""
    implicit_regression:bool = False
    """if true, use the implicit regression function"""


def extract_validation(database_pickle: str, training_filename: str):
    """
    Loads the sample database from a pickle file, filters out the training samples,
    and returns the validation arrays for time, qpos, qvel, qacc, and force.

    Parameters:
        database_pickle (str): Path to the pickled Pandas DataFrame containing the samples.
        training_filename (str): The filename (with or without path) used for training. (WITH extension)

    Returns:
        tuple: Five NumPy arrays (time, qpos, qvel, qacc, force) for validation.
    """
    # Load the DataFrame from the pickle file.
    df = pd.read_pickle(database_pickle)

    # Extract the system name from the training filename (assumes system is before '__')
    training_base = os.path.basename(training_filename).split("__")[0]

    # Filter out rows: select only rows from the same system and not from the training file.
    validation_df = df[
        (df["system"] == training_base)
        & (df["filename"] != os.path.basename(training_filename))
    ]

    # print(len(df[df['system'] == training_base]),len(validation_df))
    # Convert each column into a NumPy array by stacking the entries.
    time_arr = np.stack(validation_df["time"].values)
    qpos_arr = np.stack(validation_df["qpos"].values)
    qvel_arr = np.stack(validation_df["qvel"].values)
    qacc_arr = np.stack(validation_df["qacc"].values)
    force_arr = np.stack(validation_df["force"].values)

    return time_arr, qpos_arr, qvel_arr, qacc_arr, force_arr


# Example usage:
# Suppose 'database.pkl' is your pickled DataFrame and 'double_pendulum_pm__14188_20250217_180452.npz'
# is the training file.
# time_val, qpos_val, qvel_val, qacc_val, force_val = extract_validation("database.pkl", "double_pendulum_pm__14188_20250217_180452.npz")


if __name__ == "__main__":

    args = tyro.cli(Args)

    ## CLI validation
    if args.experiment_file == "None":
        raise ValueError(
            "experiment_file should be provided, don't hesitate to invoke --help"
        )

    with open(args.experiment_file + ".json", "r") as json_file:
        simulation_dict = json.load(json_file)

    result_name = f"result__{args.algorithm}__{args.noise_level:.1e}__{args.optimization_function}"
    if args.skip_already_done:
        if result_name in simulation_dict:
            print("already aligned")
            exit()

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

    random_seed = simulation_dict["input"]["random_seed"] + args.random_seed
    print("random seed is :", random_seed)
    num_coordinates, time_sym, symbols_matrix, catalog_repartition, extra_info = (
        xlsindy_component(mode=args.algorithm, random_seed=random_seed)
    )



    regression_function = eval(f"xlsindy.optimization.{args.optimization_function}")

    sim_data = np.load(args.experiment_file + ".npz")

    rng = np.random.default_rng(random_seed)

    # load
    imported_time = sim_data["array1"]
    imported_qpos = sim_data["array2"]
    imported_qvel = sim_data["array3"]
    imported_qacc = sim_data["array4"]
    imported_force = sim_data["array5"]

    print(
        "debug mujoco :",
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

    ## XLSINDY dependent

    if args.implicit_regression:

        solution, exp_matrix, _ = xlsindy.simulation.regression_implicite(
            theta_values=imported_qpos,
            velocity_values=imported_qvel,
            acceleration_values=imported_qacc,
            time_symbol=time_sym,
            symbol_matrix=symbols_matrix,
            catalog_repartition=catalog_repartition,
            hard_threshold=1e-3,
            regression_function=regression_function,
        )

    else:

        solution, exp_matrix, _ = xlsindy.simulation.regression_explicite(
            theta_values=imported_qpos,
            velocity_values=imported_qvel,
            acceleration_values=imported_qacc,
            time_symbol=time_sym,
            symbol_matrix=symbols_matrix,
            catalog_repartition=catalog_repartition,
            external_force=imported_force,
            hard_threshold=1e-3,
            regression_function=regression_function,
        )

    if args.biparted_graph:

        catalog_label = xlsindy.symbolic_util.label_catalog(catalog_repartition)

        ground_truth_indices = np.argwhere( extra_info["ideal_solution_vector"].flatten() != 0).flatten()
        
        b_label = ["$q_{{{}}}$".format(i) for i in range(num_coordinates)]

        print(len(catalog_label))

        link = xlsindy.optimization.bipartite_link(exp_matrix, num_coordinates, catalog_label,b_label )

        xlsindy.render.plot_bipartite_graph_svg(
            catalog_label,
            b_label,
            link,
            ground_truth_indices,
            output_file=f"bipartite_graph_{args.algorithm}_{args.optimization_function}_{args.experiment_file.split('/')[-1]}_min.svg",
            important_exclusive=True,
        )

        exit()


    # DEBUG
    # solution = extra_info["ideal_solution_vector"]

    ##--------------------------------

    model_acceleration_func, valid_model = (
        xlsindy.dynamics_modeling.generate_acceleration_function(
            solution,
            catalog_repartition,
            symbols_matrix,
            time_sym,
            lambdify_module="jax",
        )
    )
    model_dynamics_system = xlsindy.dynamics_modeling.dynamics_function_RK4_env(
        model_acceleration_func
    )

    ## Analysis of result

    result_name = f"result__{args.algorithm}__{args.noise_level:.1e}__{args.optimization_function}"

    print("result_name :", result_name)
    simulation_dict[result_name] = {}
    simulation_dict[result_name]["algoritm"] = args.algorithm
    simulation_dict[result_name]["noise_level"] = args.noise_level
    simulation_dict[result_name]["optimization_function"] = args.optimization_function
    simulation_dict[result_name]["random_seed"] = random_seed
    simulation_dict[result_name]["catalog_len"] = extra_info["catalog_len"]

    simulation_dict[result_name]["ideal_solution"] = extra_info["ideal_solution_vector"]

    if valid_model:

        model_dynamics_system = vmap(model_dynamics_system, in_axes=(1, 1), out_axes=1)


        model_acc = xlsindy.dynamics_modeling.vectorised_acceleration_generation(
            model_dynamics_system, imported_qpos, imported_qvel, imported_force
        )
        # Finally, select the columns of interest (e.g., every second column starting at index 1)
        model_acc = model_acc[:, 1::2]

        if args.validation_on_database:

            (
                validation_time,
                validation_qpos,
                validation_qvel,
                validation_qacc,
                validation_force,
            ) = extract_validation(
                "validation_database.pkl", args.experiment_file + ".npz"
            )

            validation_acc = (
                xlsindy.dynamics_modeling.vectorised_acceleration_generation(
                    model_dynamics_system,
                    validation_qpos,
                    validation_qvel,
                    validation_force,
                )
            )
            validation_acc = validation_acc[:, 1::2]

            RMSE_validation = xlsindy.result_formatting.relative_mse(
                validation_acc[3:-3], validation_qacc[3:-3]
            )

            simulation_dict[result_name]["RMSE_validation"] = RMSE_validation
            print("estimate variance on validation is : ", RMSE_validation)

        simulation_dict[result_name]["solution"] = solution
        # Estimate of the variance between model and mujoco
        RMSE_acceleration = xlsindy.result_formatting.relative_mse(
            model_acc[3:-3], imported_qacc[3:-3]
        )

        simulation_dict[result_name]["RMSE_acceleration"] = RMSE_acceleration
        print("estimate variance between mujoco and model is : ", RMSE_acceleration)

        # Sparsity difference
        non_null_term = np.argwhere(solution[:, 0] != 0).flatten()

        ideal_solution = extra_info["ideal_solution_vector"][:, 0]

        non_null_term = np.unique(
            np.concat(
                (non_null_term, np.argwhere(ideal_solution != 0).flatten()), axis=0
            ),
            axis=0,
        )

        sparsity_reference = np.count_nonzero(extra_info["ideal_solution_vector"])
        sparsity_model = np.count_nonzero(solution)

        sparsity_percentage = (
            100 * (sparsity_model - sparsity_reference) / sparsity_reference
        )
        sparsity_difference = abs(sparsity_model - sparsity_reference)
        print("sparsity difference percentage : ", sparsity_percentage)
        print("sparsity difference number : ", sparsity_difference)

        simulation_dict[result_name]["sparsity_difference"] = sparsity_difference
        simulation_dict[result_name][
            "sparsity_difference_percentage"
        ] = sparsity_percentage

        # Model RMSE comparison
        ideal_solution_norm_nn = xlsindy.result_formatting.normalise_solution(
            extra_info["ideal_solution_vector"]
        )[non_null_term]

        solution_norm_nn = xlsindy.result_formatting.normalise_solution(solution)[
            non_null_term
        ]

        RMSE_model = xlsindy.result_formatting.relative_mse(
            solution_norm_nn, ideal_solution_norm_nn
        )
        simulation_dict[result_name]["RMSE_model"] = RMSE_model
        print("RMSE model comparison : ", RMSE_model)

    if not valid_model:
        print("Skipped model verification, retrieval failed")

    simulation_dict = xlsindy.result_formatting.convert_to_strings(simulation_dict)
    print("print model ...")
    with open(args.experiment_file + ".json", "w") as file:
        json.dump(simulation_dict, file, indent=4)
