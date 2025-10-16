"""
This script is used to test the whole pipeline of the project.
An ideal trajectory is generated and then we run a regression tets

I have decided to make this script in order to confirm that the implementation of regression algorithm is correct.
The script is less bothersome than running the whole benchmarking pipeline (generating, regressing, storing, plotting,...)
"""

# tyro cly dependencies
from dataclasses import dataclass
from dataclasses import field
from typing import List
import tyro

import sys
import os 
import importlib

import mujoco
import numpy as np
import xlsindy

import matplotlib.pyplot as plt

from xlsindy.catalog import CatalogRepartition

import logging



@dataclass
class Args:
    ## Randomness
    random_seed: List[int] = field(default_factory=lambda: [2])
    """the random seed of the experiment (only used for force function)"""
    ## Catalog
    catalog_restriction: int = -1
    """the number of term in the catalog to use, if -1 use all the catalog (default -1).
    If number is less than ideal solution, the catalog is truncated to the number of ideal solution term"""
    ## Data generation
    batch_number: int = 1
    """the number of batch to generate, this is used to generate more data mainly in implicit case (default 1)"""
    mujoco_generation:bool = True
    """if true generate the data using mujoco otherwise use the theoritical generator (default true)"""
    experiment_folder: str = "None"
    """the folder where the experiment data is stored : the mujoco environment.xml file and the xlsindy_gen.py script"""
    max_time: float = 10.0
    """the maximum time for the simulation"""
    initial_condition_randomness: List[float] = field(default_factory=lambda: [0.0])
    """the randomness of the initial condition, this is used to generate a random initial condition around the initial position for each batch"""
    initial_position: List[float] = field(default_factory=lambda: [])
    """the initial position of the system"""
    forces_scale_vector: List[float] = field(default_factory=lambda: [])
    """the different scale for the forces vector to be applied, this can mimic an action mask over the system if some entry are 0"""
    forces_period: float = 3.0
    """the period for the forces function"""
    forces_period_shift: float = 0.5
    """the shift for the period of the forces function"""
    sample_number: int = 1000
    """the number of sample for the experiment (ten times the lenght of the catalog works well)"""
    ## Data regression
    optimization_function: str = "lasso_regression"
    """the regression function used in the regression"""
    algorithm: str = "xlsindy"
    """the name of the algorithm used (for the moment "xlsindy" and "sindy" are the only possible)"""
    noise_level: float = 0.0
    """the level of noise introduce in the experiment"""
    regression_type:str = "explicit"
    """if true, use the implicit regression function"""
    implicit_regression_debug:bool = False
    """if true, use the implicit regression function with debug mode"""
    implicit_regression_lamba: float = 1e-3
    """the lambda value for the implicit regression function"""

if __name__ == "__main__":

### ----------------------------------- Part 0 , load the variable -----------------------------------

# Setup logger 

    FORMAT = "[PY-XL-SINDY] [%(asctime)s] [%(levelname)s] [%(name)s] %(message)s"
    logging.basicConfig(level="INFO", format=FORMAT, stream=sys.stdout)

    args = tyro.cli(Args)

    # CLI validation
    if args.forces_scale_vector == []:
        raise ValueError(
            "forces_scale_vector should be provided, don't hesitate to invoke --help"
        )
    if args.experiment_folder == "None":
        raise ValueError(
            "experiment_folder should be provided, don't hesitate to invoke --help"
        )
    else:  # import the xlsindy_back_script
        folder_path = os.path.join(os.path.dirname(__file__), args.experiment_folder)
        sys.path.append(folder_path)

        # import the xlsindy_gen.py script
        xlsindy_gen = importlib.import_module("xlsindy_gen")

        try:
            xlsindy_component = xlsindy_gen.xlsindy_component
        except AttributeError:
            raise AttributeError(
                "xlsindy_gen.py should contain a function named xlsindy_component"
            )

        try:
            mujoco_transform = xlsindy_gen.mujoco_transform
        except AttributeError:
            mujoco_transform = None

        try:
            inverse_mujoco_transform = xlsindy_gen.inverse_mujoco_transform
        except AttributeError:
            inverse_mujoco_transform = None


        num_coordinates, time_sym, symbols_matrix, full_catalog, extra_info = (
            xlsindy_component(mode=args.algorithm, random_seed=args.random_seed)
        )

        rng = np.random.default_rng(args.random_seed)

        ## Calatog restriction
        if args.catalog_restriction >= 0:
            
            ideal_solution_binary = np.where(
                extra_info["ideal_solution_vector"] != 0, 1, 0
            ).flatten()

            if args.catalog_restriction > ideal_solution_binary.sum():
                zero_indices = np.flatnonzero(ideal_solution_binary == 0)
                chosen_indices = rng.choice(
                    zero_indices,
                    size=args.catalog_restriction - ideal_solution_binary.sum(),
                    replace=False,
                )
                ideal_solution_binary[chosen_indices] = 1

            else:
                print(
                    f"INFO : Catalog restriction is {args.catalog_restriction} but ideal solution has only {ideal_solution_binary.sum()} non-zero terms, using all the necessary catalog"
                )

            masked_catalog,_ = full_catalog.separate_by_mask(ideal_solution_binary)

            full_catalog = masked_catalog
        
            ideal_solution_vector = extra_info["ideal_solution_vector"][ideal_solution_binary==1]


        else:
            ideal_solution_vector = extra_info["ideal_solution_vector"]
        
        # Mujoco environment path
        mujoco_xml = os.path.join(folder_path, "environment.xml")

    print("INFO : Cli validated")
    ## TODO add a check for the number of forces scale vector in the input

### ----------------------- Part 1, generate the data using Mujoco or theorical ----------------------
    
    # Batch generation of data

    # Initialise 
    simulation_time_g = np.empty((0,1))
    simulation_qpos_g = np.empty((0,num_coordinates))
    simulation_qvel_g = np.empty((0,num_coordinates))
    simulation_qacc_g = np.empty((0,num_coordinates))
    force_vector_g = np.empty((0,num_coordinates))

    

    if len(args.initial_position)==0:
        args.initial_position = np.zeros((num_coordinates,2))

    # Batch generation



    if args.mujoco_generation : # Mujoco Generation
        
        # initialize Mujoco environment and controller
        mujoco_model = mujoco.MjModel.from_xml_path(mujoco_xml)
        mujoco_data = mujoco.MjData(mujoco_model)

        # Initial condition
        initial_condition = np.array(args.initial_position).reshape(num_coordinates,2) + extra_info["initial_condition"]

        if len(args.initial_condition_randomness) == 1:
            initial_condition += rng.normal(
                loc=0, scale=args.initial_condition_randomness, size=initial_condition.shape
            )
        else:
            initial_condition += rng.normal(
                loc=0, scale=np.reshape(args.initial_condition_randomness,initial_condition.shape)
            )

        # Random controller initialisation. This is the only random place of the code Everything else is deterministic (except if non deterministic solver is used)
        forces_function = xlsindy.dynamics_modeling.optimized_force_generator(
            component_count=num_coordinates,
            scale_vector=args.forces_scale_vector,
            time_end=args.max_time,
            period=args.forces_period,
            period_shift=args.forces_period_shift,
            augmentations=10, # base is 40
            random_seed=args.random_seed,
        )

        simulation_time_m = []
        simulation_qpos_m = []
        simulation_qvel_m = []
        simulation_qacc_m = []
        force_vector_m = []



        initial_qpos,initial_qvel = initial_condition[:,0].reshape(1,-1),initial_condition[:,1].reshape(1,-1)

        initial_qpos,initial_qvel,_ = inverse_mujoco_transform(initial_qpos,initial_qvel,None)

        mujoco_data.qpos = initial_qpos
        mujoco_data.qvel = initial_qvel


        def random_controller(forces_function):

            def ret(model, data):

                forces = forces_function(data.time)
                data.qfrc_applied = forces

                force_vector_m.append(forces.copy())

                simulation_time_m.append(data.time)
                simulation_qpos_m.append(data.qpos.copy())
                simulation_qvel_m.append(data.qvel.copy())
                simulation_qacc_m.append(data.qacc.copy())

            return ret

        mujoco.set_mjcb_control(
            random_controller(forces_function)
        )  # use this for the controller, could be made easier with using directly the data from mujoco.

        print("INFO : Mujoco initialized")
        while mujoco_data.time < args.max_time:
            mujoco.mj_step(mujoco_model, mujoco_data)

        print("INFO : Mujoco simulation done")

        # turn the result into a numpy array, and transform the data if needed
        simulation_qpos_m, simulation_qvel_m, simulation_qacc_m = mujoco_transform(
            np.array(simulation_qpos_m), np.array(simulation_qvel_m), np.array(simulation_qacc_m)
        )
        simulation_time_m = np.array(simulation_time_m).reshape(-1, 1)
        force_vector_m = np.array(force_vector_m)

        if len(simulation_qvel_g) >0:
            simulation_time_m += np.max(simulation_time_g)

        # Concatenate the data
        simulation_time_g = np.concatenate((simulation_time_g, simulation_time_m), axis=0)
        simulation_qpos_g = np.concatenate((simulation_qpos_g, simulation_qpos_m), axis=0)
        simulation_qvel_g = np.concatenate((simulation_qvel_g, simulation_qvel_m), axis=0)
        simulation_qacc_g = np.concatenate((simulation_qacc_g, simulation_qacc_m), axis=0)
        force_vector_g = np.concatenate((force_vector_g, force_vector_m), axis=0)



    else: # Theorical generation
        
        model_acceleration_func, valid_model = xlsindy.dynamics_modeling.generate_acceleration_function(
        ideal_solution_vector,
        full_catalog,
        symbols_matrix,
        time_sym,
        lambdify_module="numpy"
        )
        
        for i in range(args.batch_number):

            # Initial condition
            initial_condition = np.array(args.initial_position).reshape(num_coordinates,2) + extra_info["initial_condition"]

            if len(args.initial_condition_randomness) == 1:
                initial_condition += rng.normal(
                    loc=0, scale=args.initial_condition_randomness, size=initial_condition.shape
                )
            else:
                initial_condition += rng.normal(
                    loc=0, scale=np.reshape(args.initial_condition_randomness,initial_condition.shape)
                )

            # Random controller initialisation. This is the only random place of the code Everything else is deterministic (except if non deterministic solver is used)
            forces_function = xlsindy.dynamics_modeling.optimized_force_generator(
                component_count=num_coordinates,
                scale_vector=args.forces_scale_vector,
                time_end=args.max_time,
                period=args.forces_period,
                period_shift=args.forces_period_shift,
                augmentations=10, # base is 40
                random_seed=args.random_seed,
            )

            model_dynamics_system = xlsindy.dynamics_modeling.dynamics_function(model_acceleration_func,forces_function) 
            print("INFO : Theorical initialized")
            try:
                simulation_time_m, phase_values = xlsindy.dynamics_modeling.run_rk45_integration(model_dynamics_system, initial_condition, args.max_time, max_step=0.005)
            except Exception as e:
                print(f"An error occurred on the RK45 integration: {e}")
            print("INFO : Theorical simulation done")

            simulation_qpos_m = phase_values[:, ::2]
            simulation_qvel_m = phase_values[:, 1::2]

            simulation_qacc_m = np.gradient(simulation_qvel_m, simulation_time_m, axis=0, edge_order=1)

            force_vector_m = forces_function(simulation_time_m.T).T

            if len(simulation_qvel_g) >0:
                simulation_time_m += np.max(simulation_time_g)
            # Concatenate the data
            simulation_time_g = np.concatenate((simulation_time_g, simulation_time_m.reshape(-1, 1)), axis=0)
            simulation_qpos_g = np.concatenate((simulation_qpos_g, simulation_qpos_m), axis=0)
            simulation_qvel_g = np.concatenate((simulation_qvel_g, simulation_qvel_m), axis=0)
            simulation_qacc_g = np.concatenate((simulation_qacc_g, simulation_qacc_m), axis=0)
            force_vector_g = np.concatenate((force_vector_g, force_vector_m), axis=0)

    raw_sample_number = len(simulation_time_g)
    print( f"Raw simulation len {raw_sample_number}")

    # Reduce the data to the desired lenght

    subsample = raw_sample_number // args.sample_number

    if subsample == 0 :
        subsample =1

    truncation = 20

    simulation_time_g = simulation_time_g[truncation:-truncation:subsample]
    simulation_qpos_g = simulation_qpos_g[truncation:-truncation:subsample]
    simulation_qvel_g = simulation_qvel_g[truncation:-truncation:subsample]
    simulation_qacc_g = simulation_qacc_g[truncation:-truncation:subsample]
    force_vector_g = force_vector_g[truncation:-truncation:subsample]

### --------------------------- Part 2, Regresssion on the Data using xlsindy ------------------------

    regression_function = eval(f"xlsindy.optimization.{args.optimization_function}")

    rng = np.random.default_rng(args.random_seed)

    simulation_qpos_g += rng.normal(loc=0, scale=args.noise_level, size=simulation_qpos_g.shape)
    simulation_qvel_g += rng.normal(loc=0, scale=args.noise_level, size=simulation_qvel_g.shape)
    simulation_qacc_g += rng.normal(loc=0, scale=args.noise_level, size=simulation_qacc_g.shape)
    force_vector_g += rng.normal(
        loc=0, scale=args.noise_level, size=force_vector_g.shape
    )

    print("INFO : Regression function initialized")

    if args.regression_type == "implicit":

            # Quick fix to remove the external forces from the catalog
        catalog_repartition_no_force = CatalogRepartition(full_catalog.catalog_repartition[1:])
        #catalog_repartition_no_force= full_catalog

        solution, exp_matrix = xlsindy.simulation.regression_implicite(
            theta_values=simulation_qpos_g,
            velocity_values=simulation_qvel_g,
            acceleration_values=simulation_qacc_g,
            time_symbol=time_sym,
            symbol_matrix=symbols_matrix,
            catalog_repartition=catalog_repartition_no_force,
            l1_lambda=args.implicit_regression_lamba,
            debug=args.implicit_regression_debug,
        )

        print("INFO : Implicit regression done")

        solution = np.vstack([np.zeros((1, solution.shape[1])), solution])
        if args.implicit_regression_debug:
            solution = np.hstack([np.zeros((solution.shape[0],1 )), solution])

        
        # # Hack for the solution to be in the same format as the explicit one
        
        exp_matrix = np.hstack([np.zeros(( exp_matrix.shape[0],1)), exp_matrix])

        print(f"the solution is splitted into {solution.shape[1]} disjoint subspace.")

        if not args.implicit_regression_debug:

            # Add k zeros before the first row of solution (shape: catalog_size, k)

            solution, _  = xlsindy.simulation.combine_best_fit(solution,ideal_solution_vector)

            solution[0,0] = -1.0    



    elif args.regression_type == "explicit":
        
        solution, exp_matrix = xlsindy.simulation.regression_explicite(
            theta_values=simulation_qpos_g,
            velocity_values=simulation_qvel_g,
            acceleration_values=simulation_qacc_g,
            time_symbol=time_sym,
            symbol_matrix=symbols_matrix,
            catalog_repartition=full_catalog,
            external_force=force_vector_g,
            regression_function=regression_function,
        )

    elif args.regression_type == "mixed":

        solution, exp_matrix = xlsindy.simulation.regression_mixed(
            theta_values=simulation_qpos_g,
            velocity_values=simulation_qvel_g,
            acceleration_values=simulation_qacc_g,
            time_symbol=time_sym,
            symbol_matrix=symbols_matrix,
            catalog_repartition=full_catalog,
            external_force=force_vector_g,
            regression_function=regression_function,
            ideal_solution_vector=ideal_solution_vector,
        )

    print("DEBUG : print a bunch of information")
    print(solution.shape)
    print(exp_matrix.shape)
    print(ideal_solution_vector.shape)
    # Apply an hardtreshold
    hard_treshold=1e-3
    solution = np.where(np.abs(solution)/np.linalg.norm(solution)>hard_treshold,solution,0)
    print("INFO : Regression done")

    #Temporary code for implicit regression debugging
    if args.implicit_regression_debug:

        # Temporary disabled 
        fig, axs = plt.subplots(3, 3,figsize=(10, 10),height_ratios=[1,4,4])
        fig.suptitle("Experiment Results")

        graph = {
            "position":axs[0,0],
            "solution_matrix":axs[1,0],
            "sparsity_matrix":axs[1,1],
            "solution":axs[2,0],
            "sparsity_solution":axs[2,1],
            "solution_sparsity_analisy":axs[2,2],
        }

        solution_matrix = solution - np.diag(np.ones(solution.shape[0]))

        col_max = np.max(np.abs(solution_matrix),axis=0)
        col_max[col_max == 0] = 1.0
        solution_matrix_normalised=solution_matrix / col_max

        solution_matrix_normalised[np.abs(solution_matrix)<1e-3] = 0.0

        sparsity_solution_matrix = np.where(solution_matrix_normalised!=0,1,0)
        sparsity_solution = np.where(ideal_solution_vector!=0,1,0)

        sparsisty_analysis = np.where(sparsity_solution+sparsity_solution_matrix==2,1,0) + \
                             np.where(sparsity_solution_matrix-sparsity_solution==-1,-1,0) + \
                             np.where(sparsity_solution-sparsity_solution_matrix==-1,-1,0)

        compare_matrix = np.abs(solution_matrix_normalised) - np.abs(ideal_solution_vector)/np.max(np.abs(ideal_solution_vector))

        graph["solution_matrix"].set_title("Solution Matrix")
        graph["solution_matrix"].imshow(np.abs(compare_matrix), aspect="equal", cmap="viridis")

        graph["sparsity_matrix"].set_title("Sparsity Matrix")
        graph["sparsity_matrix"].imshow(sparsity_solution_matrix, aspect="equal", cmap="viridis")

        graph["solution_sparsity_analisy"].set_title("Sparsity anlysis Matrix")
        graph["solution_sparsity_analisy"].imshow(sparsisty_analysis, aspect="equal", cmap="viridis")
        #graph["solution_sparsity_analisy"].grid(axis='x')

        graph["solution"].set_title("Solution")
        graph["solution"].imshow(np.abs(ideal_solution_vector), aspect="auto", cmap="viridis")

        graph["sparsity_solution"].set_title("Sparsity Solution")
        graph["sparsity_solution"].imshow(sparsity_solution, aspect="auto", cmap="viridis")

        graph["position"].set_title("Position") 
        graph["position"].plot(simulation_time_g,simulation_qpos_g)

        filename = f"single_test_result/experiment_result_{args.experiment_folder.split('/')[1]}_{args.regression_type }_{'mujoco' if args.mujoco_generation else 'theory'}_{args.optimization_function}_{args.algorithm}"

        fig.savefig(filename+".svg")
        np.save(filename+".npy", solution_matrix)
        np.save(filename+"_ideal_solution.npy", ideal_solution_vector)

        exit() # exit because the implicit regression is not compatible with the rest of the code
    #End of temporary code 

    # Not used right now
    model_acceleration_func, valid_model = (
    xlsindy.dynamics_modeling.generate_acceleration_function(
        solution,
        full_catalog,
        symbols_matrix,
        time_sym,
        lambdify_module="jax",
    )
    )

### -------------------------------------- Part 3, Result analisys -----------------------------------

    # Can t be used for the moment when using the implicit regression 

    # Ideal Residulas (only for debugging purposes)
    exp_matrix_amp,forces_vector_g = xlsindy.optimization.amputate_experiment_matrix(exp_matrix,0)

    print("forces difference",np.linalg.norm(forces_vector_g.flatten()-force_vector_g.T.flatten()))


    ideal_residuals = exp_matrix @ ideal_solution_vector
    residuals = exp_matrix @ solution

    forces_vector_g_norm = np.linalg.norm(forces_vector_g)

    forces_vector_g_norm = 1 if forces_vector_g_norm<1e-4 else forces_vector_g_norm

    ideal_residuals_norm = np.linalg.norm(ideal_residuals)/forces_vector_g_norm
    print("Ideal Residuals : ", ideal_residuals_norm )

    # Correlate in order to verify no offset DEPRECATED
    # correlate =  np.correlate(LHS.flatten(),RHS.flatten(),"full")
    # print("max overlap :", np.argmax(correlate) - (len(RHS) - 1))

    # Residuals
    residuals_norm = np.linalg.norm(residuals)/forces_vector_g_norm
    print("Residuals : ", residuals_norm)

    # Sparsity of the model 
    sparsity_reference = np.count_nonzero(ideal_solution_vector)
    sparsity_model = np.count_nonzero(solution)

    sparsity_percentage = (
        100 * (sparsity_model - sparsity_reference) / sparsity_reference
    )
    sparsity_difference = abs(sparsity_model - sparsity_reference)
    print("sparsity difference percentage : ", sparsity_percentage)
    print("sparsity difference number : ", sparsity_difference)

    # Model RMSE comparison

    non_null_term = np.argwhere(solution.flatten() != 0)

    non_null_term = np.unique(
        np.concat(
            (non_null_term, np.argwhere(ideal_solution_vector.flatten() != 0)), axis=0
        ),
        axis=0,
    )

    ideal_solution_norm = xlsindy.result_formatting.normalise_solution(
        ideal_solution_vector
    )

    solution_norm = xlsindy.result_formatting.normalise_solution(solution)

    RMSE_model = xlsindy.result_formatting.relative_mse(
        solution_norm[non_null_term], ideal_solution_norm[non_null_term]
    )

    print("RMSE model comparison : ", RMSE_model)

### ----------------------------------------- Part 4, Render -----------------------------------------

    # Function catalog rendering
    fig, axs = plt.subplots(4, 1,figsize=(10, 10))
    fig.suptitle("Experiment Results")

    graph = {
        "model_comp":axs[0],
        "residuals":axs[1],
        "ideal_residuals":axs[2],
        "position":axs[3],
    }

    graph["model_comp"].set_title("Model Comparison")

    graph["model_comp"].bar(
        np.arange(len(solution_norm)),
        solution_norm[:, 0],
        width=1,
        label="Found Model",
    )

    bar_height_found = np.abs(solution) / np.max(np.abs(solution))
    graph["model_comp"].bar(
        np.arange(len(ideal_solution_norm)),
        ideal_solution_norm[:, 0],
        width=0.5,
        label="True Model",
    )

    graph["model_comp"].legend(loc="upper right")

    graph["residuals"].set_title("Residuals")

    res = residuals.reshape(num_coordinates,-1).T
    ideal_res = ideal_residuals.reshape(num_coordinates,-1).T

    for i in range(num_coordinates):

        graph["residuals"].plot(
            simulation_time_g,
            res[:,i],
            label=f"Residuals q{i}",
        )
        graph["ideal_residuals"].plot(
            simulation_time_g,
            ideal_res[:,i],
            label=f"Ideal Residuals q{i}",
        )

    graph["model_comp"].text(0.01, 0.05, f"RMSE model comparison : {RMSE_model:.2e}",
        transform=graph["model_comp"].transAxes,
        fontsize=12,
        verticalalignment='bottom',
        horizontalalignment='left',
        bbox=dict(facecolor='white', alpha=0.7))

    graph["residuals"].text(0.01, 0.05, f"Residuals : {residuals_norm:.2e}",
        transform=graph["residuals"].transAxes,
        fontsize=12,
        verticalalignment='bottom',
        horizontalalignment='left',
        bbox=dict(facecolor='white', alpha=0.7))
    
    graph["ideal_residuals"].text(0.01, 0.05, f"Ideals residuals : {ideal_residuals_norm:.2e}",
        transform=graph["ideal_residuals"].transAxes,
        fontsize=12,
        verticalalignment='bottom',
        horizontalalignment='left',
        bbox=dict(facecolor='white', alpha=0.7))

    #graph["debug"].plot(correlate)

    graph["residuals"].legend(loc="upper right")
    graph["ideal_residuals"].legend(loc="upper right")

    graph["position"].set_title("Position")
    graph["position"].plot(simulation_time_g, simulation_qpos_g)

    fig.savefig(f"single_test_result/experiment_result_{args.experiment_folder.split('/')[1]}_{args.regression_type }_{'mujoco' if args.mujoco_generation else 'theory'}_{args.optimization_function}_{args.algorithm}.svg")
    plt.show()


