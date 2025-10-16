""" 
(DEPRECATED) *this script has been deprecated and replaced by the whole framework presented in folder README.md*

The goal of this script is to align xl_sindy algorithm with the Mujoco environment.
The script takes in input :
- the simulation folder containing the mujoco environment.xml file and the xlsindy_gen.py script
- the way forces function should be created
- some optional hyperparameters

This script enable the user to check that mujoco environment and lagrangian can align (check the validity of mujoco transform and so on).
"""
#tyro cly dependencies
from dataclasses import dataclass
from dataclasses import field
from typing import List
import tyro

import sys
import os
import importlib

import mujoco
import mujoco.viewer
import time
import numpy as np 
import xlsindy

import matplotlib.pyplot as plt


# loggin purpose
import json
from datetime import datetime



@dataclass
class Args:
    experiment_folder: str = None
    """the folder where the experiment data is stored : the mujoco environment.xml file and the xlsindy_gen.py script"""
    max_time: float = 10.0
    """the maximum time for the simulation"""
    real_mujoco_time: bool = True
    """if True, the simulation will be done in real time, otherwise, the simulation will be done as fast as possible"""
    forces_scale_vector: List[float] = field(default_factory=lambda: None)
    """the different scale for the forces vector to be applied, this can mimic an action mask over the system if some entry are 0"""
    forces_period: float = 3.0
    """the period for the forces function"""
    forces_period_shift: float = 0.5
    """the shift for the period of the forces function"""
    generate_ideal_path: bool = False
    """if True, the ideal simulation from the lagrangian provided will be generated"""
    regression:bool = True
    """if True, generate the lagrangian Sindy regression"""
    force_ideal_solution:bool = False
    """if True, override the regression and force the ideal model (for debug purpose of mujoco/rk45sim)"""
    plot:bool = False
    """if True, plot on pyplot"""
    export_json:bool = True
    """if True, export the json of the result and environment information"""
    mujoco_viewer:bool = False
    """if True, open a mujoco viewer for the simulation"""
    random_seed:List[int] = field(default_factory=lambda:[2])
    """the random seed of the experiment (only used for force function)"""
    optimization_function:str = "lasso_regression"
    """the regression function used in the regression"""


if __name__ == "__main__":

    args = tyro.cli(Args)

    simulation_dict = {} # the simulation dictionnary storing everything about the simulation
    #print(args)
    simulation_dict["input"] = {}
    simulation_dict["input"]["forces_scale_vector"]=args.forces_scale_vector
    simulation_dict["input"]["max_time"] = args.max_time
    simulation_dict["input"]["forces_period"] = args.forces_period
    simulation_dict["input"]["forces_period_shift"] = args.forces_period_shift
    simulation_dict["input"]["experiment_folder"] = args.experiment_folder.split("/")[-1]

    # CLI validation
    if args.forces_scale_vector is None:
        raise ValueError("forces_scale_vector should be provided, don't hesitate to invoke --help")
    if args.experiment_folder is None:
        raise ValueError("experiment_folder should be provided, don't hesitate to invoke --help")
    else: # import the xlsindy_back_script
        folder_path = os.path.join(os.path.dirname(__file__), args.experiment_folder)
        sys.path.append(folder_path)

        # import the xlsindy_gen.py script
        xlsindy_gen = importlib.import_module("xlsindy_gen")

        try:
            xlsindy_component = xlsindy_gen.xlsindy_component
        except AttributeError:
            raise AttributeError("xlsindy_gen.py should contain a function named xlsindy_component")
        
        try:
            mujoco_transform = xlsindy_gen.mujoco_transform
        except AttributeError:
            mujoco_transform = None

        try:
            forces_wrapper = xlsindy_gen.forces_wrapper
        except AttributeError:
            forces_wrapper = None
        
        num_coordinates, time_sym, symbols_matrix, full_catalog, extra_info = xlsindy_component()

        simulation_dict["environment"] = {}
        simulation_dict["environment"]["coordinate_number"] = num_coordinates
        simulation_dict["environment"]["extra_info"]=extra_info
        simulation_dict["environment"]["catalog_len"]=len(full_catalog)


        # Mujoco environment path
        mujoco_xml = os.path.join(folder_path, "environment.xml")

    regression_function=eval(f"xlsindy.optimization.{args.optimization_function}")

    # Random controller initialisation. This is the only random place of the code Everything else is deterministic (except if non deterministic solver is used)
    forces_function = xlsindy.dynamics_modeling.optimized_force_generator(
        component_count=num_coordinates,
        scale_vector=args.forces_scale_vector,
        time_end=args.max_time,
        period=args.forces_period,
        period_shift=args.forces_period_shift,
        augmentations=40,
        random_seed=args.random_seed
    )


    # initialize Mujoco environment and controller

    mujoco_model = mujoco.MjModel.from_xml_path(mujoco_xml)
    mujoco_data = mujoco.MjData(mujoco_model)

    mujoco_time = []
    mujoco_qpos = []
    mujoco_qvel = []
    mujoco_qacc = []
    force_vector =[]

    def random_controller(forces_function):

        def ret(model, data):

            forces = forces_function(data.time)
            data.qfrc_applied = forces

            force_vector.append(forces.copy())

            mujoco_time.append(data.time)
            mujoco_qpos.append(data.qpos.copy())
            mujoco_qvel.append(data.qvel.copy())
            mujoco_qacc.append(data.qacc.copy())

        return ret
    
    mujoco.set_mjcb_control(random_controller(forces_function)) # use this for the controller, could be made easier with using directly the data from mujoco.

    # Viewer of the experiment

    if args.mujoco_viewer:

        with mujoco.viewer.launch_passive(mujoco_model, mujoco_data) as viewer:

            time_start_simulation = time.time()
            while viewer.is_running() and mujoco_data.time < args.max_time:
        
                mujoco.mj_step(mujoco_model, mujoco_data)
                viewer.sync()
                
                if args.real_mujoco_time:
                    time_until_next_step = mujoco_model.opt.timestep - (time.time() - time_start_simulation)
                    if time_until_next_step > 0:
                        time.sleep(time_until_next_step)

            viewer.close()

    else:
        while mujoco_data.time < args.max_time:
            mujoco.mj_step(mujoco_model, mujoco_data)


    # turn the result into a numpy array
    mujoco_time = np.array(mujoco_time)
    mujoco_qpos = np.array(mujoco_qpos)
    mujoco_qvel = np.array(mujoco_qvel)
    mujoco_qacc = np.array(mujoco_qacc)
    force_vector = np.array(force_vector)

    mujoco_qpos,mujoco_qvel,mujoco_qacc,force_vector = mujoco_transform(mujoco_qpos,mujoco_qvel,mujoco_qacc,force_vector)

    nb_t = len(mujoco_time)

    surfacteur = len(full_catalog) * 10
    subsample = nb_t // surfacteur
    start_truncation = 2

    mujoco_time = mujoco_time[start_truncation::subsample]
    mujoco_qpos = mujoco_qpos[start_truncation::subsample]
    mujoco_qvel = mujoco_qvel[start_truncation::subsample]
    mujoco_qacc = mujoco_qacc[start_truncation::subsample]
    force_vector = force_vector[start_truncation::subsample]

    # Volume of the explored space

    phase_portrait_explored = np.concatenate((mujoco_qpos,mujoco_qvel),axis=1)

    estimated_volumes = xlsindy.result_formatting.estimate_volumes(phase_portrait_explored,5) # 5th nearest neighboor density estimation
    print("estimated volumes is :",estimated_volumes)
    simulation_dict["result"] = {}
    simulation_dict["result"]["exploration_volumes"] = estimated_volumes


    if args.regression:
        # Goes into the xlsindy regression

        if not args.force_ideal_solution:

           
            solution, exp_matrix, _ = xlsindy.simulation.execute_regression(
            theta_values=mujoco_qpos,
            velocity_values = mujoco_qvel,
            acceleration_values = mujoco_qacc,
            time_symbol=time_sym,
            symbol_matrix=symbols_matrix,
            catalog=full_catalog,
            external_force= force_vector,
            hard_threshold = 1e-3,
            apply_normalization = True,
            regression_function=regression_function
            )
        
        else:
            solution=extra_info["ideal_solution_vector"]


        # Compare the result with the base environment 
        modele_fit,friction_matrix = xlsindy.catalog_gen.create_solution_expression(solution[:, 0], full_catalog,num_coordinates=num_coordinates,first_order_friction=True)

        model_acceleration_func, _ = xlsindy.euler_lagrange.generate_acceleration_function(modele_fit, symbols_matrix, time_sym,first_order_friction=friction_matrix,lambdify_module="jax")
        model_dynamics_system = xlsindy.dynamics_modeling.dynamics_function_RK4_env(model_acceleration_func) 
        

        model_acc = []

        for i in range(len(mujoco_time)): # skip start

            base_vector = np.ravel(np.column_stack((mujoco_qpos[i],mujoco_qvel[i])))

            model_acc+= [model_dynamics_system(base_vector,force_vector[i])]

        model_acc = np.array(model_acc)

        model_acc = model_acc[:,1::2]

        ## Numerical value as a result

        
        # Estimate of the variance between model and mujoco
        RMSE_acceleration = xlsindy.result_formatting.relative_mse(model_acc[3:-3],mujoco_qacc[3:-3])

        simulation_dict["result"]["RMSE_acceleration"] = RMSE_acceleration

        print("estimate variance between mujoco and model is : ",RMSE_acceleration)

        # Sparsity difference
        non_null_term = np.argwhere(solution != 0) 

        if extra_info is not None:
            ideal_solution = extra_info["ideal_solution_vector"]

            non_null_term=np.unique(np.concat((non_null_term,np.argwhere(ideal_solution != 0 )),axis=0),axis=0)

        sparsity_reference = np.count_nonzero( extra_info["ideal_solution_vector"] )
        sparsity_model = np.count_nonzero(solution)

        sparsity_percentage = 100*(sparsity_model-sparsity_reference)/sparsity_reference
        sparsity_difference = abs(sparsity_model-sparsity_reference)
        print("sparsity difference percentage : ",sparsity_percentage)
        print("sparsity difference number : ",sparsity_difference)

        simulation_dict["result"]["sparsity_difference"] = sparsity_difference
        simulation_dict["result"]["sparsity_difference_percentage"] = sparsity_percentage

        if args.generate_ideal_path : 

            rk45_time_values, rk45_phase_values = xlsindy.dynamics_modeling.run_rk45_integration(model_dynamics_system, extra_info["initial_condition"], args.max_time, max_step=0.01)
            rk45_theta_values = rk45_phase_values[:, ::2]
            rk45_velocity_values = rk45_phase_values[:, 1::2]

    # model comparison RMSE
        ideal_solution_norm_nn = xlsindy.result_formatting.normalise_solution(extra_info["ideal_solution_vector"])[*non_null_term.T]
        solution_norm_nn = xlsindy.result_formatting.normalise_solution(solution)[*non_null_term.T]

        RMSE_model = xlsindy.result_formatting.relative_mse(ideal_solution_norm_nn,solution_norm_nn)
        print("RMSE model comparison : ",RMSE_model)

        simulation_dict["result"]["RMSE_model"] = RMSE_model

        simulation_dict["result"]["ideal_solution_norm_nn"] = ideal_solution_norm_nn
        simulation_dict["result"]["solution_norm_nn"] = solution_norm_nn

    if args.export_json:

        now = datetime.now()
        timestamp = now.strftime("%Y%m%d_%H%M%S")

        filename=f"result/{simulation_dict["input"]["experiment_folder"]}_{timestamp}.json"

        simulation_dict = xlsindy.result_formatting.convert_to_strings(simulation_dict)

        with open(filename, 'w') as file:
            json.dump(simulation_dict, file, indent=4)

    if args.plot:

        print("Regression finished plotting in progress ... ")
        # Matplot plotting for the results

        fig, ax = plt.subplots()
        for i in range(num_coordinates):

            if args.regression:
                ax.plot(mujoco_time, model_acc[:,i],label=f"model $\\ddot{{q}}_{i}$")
        
            ax.plot(mujoco_time, mujoco_qacc[:,i],label=f"mujoco $\\ddot{{q}}_{i}$")


        ax.legend()

        fig, ax = plt.subplots()
        for i in range(num_coordinates):
            ax.plot(mujoco_time, mujoco_qvel[:,i],label=f"mujoco $\\dot{{q}}_{i}$")

            if args.regression:
                ax.plot(rk45_time_values, rk45_velocity_values[:,i],label=f"model $\\dot{{q}}_{i}$")
        ax.legend()


        fig, ax = plt.subplots()
        for i in range(num_coordinates):
            ax.plot(mujoco_time, mujoco_qpos[:,i],label=f"q_{i}")

            if args.regression & args.generate_ideal_path:
                ax.plot(rk45_time_values, rk45_theta_values[:,i],label=f"rk_{{45}}q_{i}")
        ax.legend()


        fig, ax = plt.subplots()    

        if args.regression:

            non_null_term = np.argwhere(solution != 0) 

            if extra_info is not None:
                ideal_solution_vector = extra_info["ideal_solution_vector"]

                non_null_term=np.unique(np.concat((non_null_term,np.argwhere(ideal_solution_vector != 0 )),axis=0),axis=0)

                ax.bar(np.arange(len(non_null_term)), xlsindy.result_formatting.normalise_solution(ideal_solution_vector)[*non_null_term.T], width=1, label="True Model")

            ax.bar(np.arange(len(non_null_term)), xlsindy.result_formatting.normalise_solution(solution)[*non_null_term.T], width=0.5, label="Model Found")
            ax.legend()



            catalog_string = xlsindy.catalog_gen.label_catalog(full_catalog,non_null_term)

            # Set x-axis tick label
            ax.set_xticklabels(catalog_string)
            ax.set_xticks(np.arange(len(non_null_term)))
            ax.tick_params(labelrotation=90)
            ax.set_xlabel("Function from catalog")

        plt.tight_layout()
        plt.show()  