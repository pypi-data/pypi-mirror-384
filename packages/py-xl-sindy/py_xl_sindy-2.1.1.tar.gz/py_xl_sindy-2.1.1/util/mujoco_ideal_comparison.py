"""
This script is made in order to verify that mujoco and theorical model are aligned.
It can also be used to verify the RK45 integration of the system.

TODO : could be nice to finish this script properly but both converge...
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

@dataclass
class Args:
    ## Randomness
    random_seed: List[int] = field(default_factory=lambda: [2])
    """the random seed of the experiment (only used for force function)"""
    ## Data generation
    experiment_folder: str = "None"
    """the folder where the experiment data is stored : the mujoco environment.xml file and the xlsindy_gen.py script"""
    initial_position: List[float] = field(default_factory=lambda: [])
    """the initial position of the system"""
    max_time: float = 10.0
    """the maximum time for the simulation"""
    forces_scale_vector: List[float] = field(default_factory=lambda: [])
    """the different scale for the forces vector to be applied, this can mimic an action mask over the system if some entry are 0"""
    forces_period: float = 3.0
    """the period for the forces function"""
    forces_period_shift: float = 0.5
    """the shift for the period of the forces function"""

if __name__ == "__main__":

### ----------------------------------- Part 0 , load the variable ----------------------------------- 

    args = tyro.cli(Args)

### ------------------------------ Part 1, generate the data using Mujoco ----------------------------

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
            xlsindy_component(random_seed=args.random_seed)
        )

        # Mujoco environment path
        mujoco_xml = os.path.join(folder_path, "environment.xml")

    ## TODO add a check for the number of forces scale vector in the input
    
    # Random controller initialisation. This is the only random place of the code Everything else is deterministic (except if non deterministic solver is used)
    forces_function = xlsindy.dynamics_modeling.optimized_force_generator(
        component_count=num_coordinates,
        scale_vector=args.forces_scale_vector,
        time_end=args.max_time,
        period=args.forces_period,
        period_shift=args.forces_period_shift,
        augmentations=10, # base 40
        random_seed=args.random_seed,
    )

    # initial condition
    initial_condition = np.array(args.initial_position).reshape(num_coordinates,2) + extra_info["initial_condition"]

    # initialize Mujoco environment and controller

    mujoco_model = mujoco.MjModel.from_xml_path(mujoco_xml)
    mujoco_data = mujoco.MjData(mujoco_model)

    mujoco_time = []
    mujoco_qpos = []
    mujoco_qvel = []
    mujoco_qacc = []
    force_vector = []

    initial_qpos,initial_qvel = initial_condition[:,0].reshape(1,-1),initial_condition[:,1].reshape(1,-1)

    initial_qpos,initial_qvel,_ = inverse_mujoco_transform(initial_qpos,initial_qvel,None)

    mujoco_data.qpos = initial_qpos
    mujoco_data.qvel = initial_qvel

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

    mujoco.set_mjcb_control(
        random_controller(forces_function)
    )  # use this for the controller, could be made easier with using directly the data from mujoco.

    while mujoco_data.time < args.max_time:
        mujoco.mj_step(mujoco_model, mujoco_data)

    # turn the result into a numpy array
    mujoco_time = np.array(mujoco_time)
    mujoco_qpos = np.array(mujoco_qpos)
    mujoco_qvel = np.array(mujoco_qvel)
    mujoco_qacc = np.array(mujoco_qacc)
    force_vector = np.array(force_vector)

    mujoco_qpos, mujoco_qvel, mujoco_qacc = mujoco_transform(
        mujoco_qpos, mujoco_qvel, mujoco_qacc
    )

    ## No need this part
    # raw_sample_number = len(mujoco_time)

    # subsample = raw_sample_number // args.sample_number
    # start_truncation = 2

    # mujoco_time = mujoco_time[start_truncation::subsample]
    # mujoco_qpos = mujoco_qpos[start_truncation::subsample]
    # mujoco_qvel = mujoco_qvel[start_truncation::subsample]
    # mujoco_qacc = mujoco_qacc[start_truncation::subsample]
    # force_vector = force_vector[start_truncation::subsample]

### ------------------------------ Part 2, generate the data using Theory ----------------------------

    model_acceleration_func, valid_model = xlsindy.dynamics_modeling.generate_acceleration_function(
        extra_info["ideal_solution_vector"],
        full_catalog,
        symbols_matrix,
        time_sym,
        lambdify_module="numpy"
        )
    
    if not valid_model:
        print("-----------------------------------------------The model is not valid-------------------------------------------------------------------------------------------------------------------------------------------------------------------")

    model_dynamics_system = xlsindy.dynamics_modeling.dynamics_function(model_acceleration_func,forces_function) 

    try:
        time_values, phase_values = xlsindy.dynamics_modeling.run_rk45_integration(model_dynamics_system, initial_condition, args.max_time, max_step=0.01)
    except Exception as e:
        print(f"An error occurred on the RK45 integration: {e}")

    theta_values = phase_values[:, ::2]
    velocity_values = phase_values[:, 1::2]

    acceleration_values = np.gradient(velocity_values, time_values, axis=0, edge_order=1)

### ------------------------------ Part 3, Render ----------------------------

    fig, axs = plt.subplots(4, 2, figsize=(12, 8))

    fig.suptitle("Mujoco Experiment Results")

    axs[0,0].plot(mujoco_time, mujoco_qpos, label="Mujoco Position")
    axs[1,0].plot(mujoco_time, mujoco_qvel, label="Mujoco Velocity")
    axs[2,0].plot(mujoco_time, mujoco_qacc, label="Mujoco Acceleration")
    axs[3,0].plot(mujoco_time, force_vector, label="Forces")

    axs[0,0].plot(time_values, theta_values, label="Theorical Position")
    axs[1,0].plot(time_values, velocity_values, label="Theorical Velocity")
    axs[2,0].plot(time_values, acceleration_values, label="Theorical Acceleration")

    axs[0,0].legend()
    axs[1,0].legend()
    axs[2,0].legend()
    axs[3,0].legend()

    # Interpolate the “other” signals onto mujoco_time

    theta_interp = np.empty((len(mujoco_time), num_coordinates))
    vel_interp = np.empty((len(mujoco_time), num_coordinates))
    acc_interp = np.empty((len(mujoco_time), num_coordinates))

    for i in range(num_coordinates):

        theta_interp[:,i] = np.interp(mujoco_time.flatten(), time_values.flatten(), theta_values[:,i])
        vel_interp[:,i]   = np.interp(mujoco_time.flatten(), time_values.flatten(), velocity_values[:,i])
        acc_interp[:,i]   = np.interp(mujoco_time.flatten(), time_values.flatten(), acceleration_values[:,i])

    # Compute residuals/differences
    pos_diff = mujoco_qpos - theta_interp
    vel_diff = mujoco_qvel - vel_interp
    acc_diff = mujoco_qacc - acc_interp

    axs[0,1].plot(mujoco_time, pos_diff, label="Position Δ")
    axs[1,1].plot(mujoco_time, vel_diff, label="Velocity Δ")
    axs[2,1].plot(mujoco_time, acc_diff, label="Acceleration Δ")

    axs[0,1].legend()
    axs[1,1].legend()
    axs[2,1].legend()


    fig.savefig("mujoco_th_comp.svg")

    plt.show()