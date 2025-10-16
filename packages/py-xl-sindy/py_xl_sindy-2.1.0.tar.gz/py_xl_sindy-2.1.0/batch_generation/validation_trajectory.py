""" 
This scripts generate a validation trajectory from mujoco and compare it with trajectory from all the retrieved model
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
import cv2

import numpy as np 
import xlsindy

import matplotlib.pyplot as plt
import matplotlib.cm as cm
import matplotlib.gridspec as gridspec

import xlsindy.result_formatting

# loggin purpose
from datetime import datetime
import json

def auto_zoom_viewport(ax, x, y, margin=0.5):
    """
    Automatically zooms the viewport for a given plot.

    Parameters:
        ax (matplotlib.axes.Axes): The Axes object to modify.
        x (array-like): X data values.
        y (array-like): Y data values.
        margin (float): Additional margin (percentage of y-range) to add around the min/max y-values.
    """
    y_min, y_max = np.min(y), np.max(y)
    y_range = y_max - y_min
    y_margin = y_range * margin

    ax.set_xlim(np.min(x), np.max(x))  # Keep x-limits to full range
    ax.set_ylim(y_min - y_margin, y_max + y_margin)  # Adjust y-limits with margin

def generate_colors_for_experiments(experiments):
    """
    Generate a dictionary mapping each experiment to a unique color based on algorithm and optimization function,
    with darkness varying according to noise level.

    Parameters:
    experiments (dict): Dictionary where keys are experiment names and values contain "noise_level", 
                        "algoritm", and "optimization_function".

    Returns:
    dict: Mapping of experiment names to RGB color values.
    """
    # Extract unique algorithm and optimization function combinations
    unique_combos = list(set((exp["algoritm"], exp["optimization_function"]) for exp in experiments.values()))
    
    # Assign a unique base color for each (algorithm, optimization_function) pair
    base_colors = {combo: cm.tab10(i) for i, combo in enumerate(unique_combos)}

    # Determine unique noise levels sorted from weakest to strongest
    unique_noise_levels = sorted(set(exp["noise_level"] for exp in experiments.values()))
    noise_attenuation = {lvl: 1 - (i / len(unique_noise_levels)) * 0.66 for i, lvl in enumerate(unique_noise_levels)}

    # Assign colors to experiments
    for exp_name, exp in experiments.items():
        base_color = np.array(base_colors[(exp["algoritm"], exp["optimization_function"])])
        attenuation_factor = noise_attenuation[exp["noise_level"]]
        darkened_color = base_color[:3] * attenuation_factor  # Apply attenuation to RGB only
        exp["color"] = (*darkened_color, base_color[3])  # Keep original alpha value



@dataclass
class Args:
    experiment_file: str = "None"
    """the experiment file (without extension)"""
    max_time: float = 10.0
    """the maximum time for the validation simulation"""
    random_seed:List[int] = field(default_factory=lambda:[])
    """the random seed to add for the force function (only used for force function)"""
    plot:bool = False
    """if True, plot the different validation trajectories"""
    skip_already_done:bool = False
    """if true, skip the experiment if already present in the result file"""
    record:bool = False
    """if true, record the video of the experiment"""

def convert_numbers(data):
    if isinstance(data, dict):
        return {key: convert_numbers(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [convert_numbers(item) for item in data]
    else:
        # Try converting to int or float
        try:
            if "." in str(data):  # If it has a decimal point, try float
                return float(data)
            return int(data)  # Otherwise, try int
        except (ValueError, TypeError):
            return data  # Return as is if conversion fails


if __name__ == "__main__":

    args = tyro.cli(Args)

    # CLI validation
    if args.experiment_file == "None":
        raise ValueError("experiment_file should be provided, don't hesitate to invoke --help")

    with open(args.experiment_file+".json", 'r') as json_file:
        simulation_dict = json.load(json_file)

        simulation_dict = convert_numbers(simulation_dict)

    folder_path = os.path.join(os.path.dirname(__file__), "mujoco_align_data/"+simulation_dict["input"]["experiment_folder"])
    sys.path.append(folder_path)

    # import the xlsindy_gen.py script
    xlsindy_gen = importlib.import_module("xlsindy_gen")

    try:
        xlsindy_component = eval(f"xlsindy_gen.xlsindy_component")
    except AttributeError:
        raise AttributeError(f"xlsindy_gen.py should contain a function named xlsindy_component")
    try:
        mujoco_transform = xlsindy_gen.mujoco_transform
    except AttributeError:
        mujoco_transform = None

    try:
        forces_wrapper = xlsindy_gen.forces_wrapper
    except AttributeError:
        forces_wrapper = None
    
    num_coordinates, time_sym, symbols_matrix, catalog_repartition, extra_info = xlsindy_component()       

    forces_function = xlsindy.dynamics_modeling.optimized_force_generator(
        component_count=num_coordinates,
        scale_vector=simulation_dict["input"]["forces_scale_vector"],
        time_end=args.max_time,
        period=simulation_dict["input"]["forces_period"],
        period_shift=simulation_dict["input"]["forces_period_shift"],
        augmentations=40,
        random_seed=simulation_dict["input"]["random_seed"]+args.random_seed
    ) 

    mujoco_xml = os.path.join(folder_path, "environment.xml")


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

    #compare with sindy 

    # Viewer of the experiment

    if args.record:

        height=720
        width=1280

        camera = mujoco.MjvCamera()
        camera.type = mujoco.mjtCamera.mjCAMERA_FIXED
        camera.fixedcamid = 0  # use the first camera defined in the model

        fps = 60
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        video = cv2.VideoWriter("poster_figure/trajectory_validation.mp4", fourcc, fps, (width, height))
        C=0
        with mujoco.Renderer(mujoco_model,height,width) as renderer:

            # Create scene and camera; force use of the first (fixed) camera from the model

            while mujoco_data.time < args.max_time:
                mujoco.mj_step(mujoco_model, mujoco_data)
                # Update scene using the current simulation state and camera view
                if C < mujoco_data.time * fps:
                    renderer.update_scene(mujoco_data, 0)
                    # Convert RGB to BGR for OpenCV and write the frame
                    video.write(cv2.cvtColor(renderer.render(), cv2.COLOR_RGB2BGR))
                    C+=1

        video.release()

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

    #phase for comparison
    mujoco_phase = np.zeros((mujoco_qpos.shape[0],mujoco_qpos.shape[1]+mujoco_qvel.shape[1]))

    mujoco_phase[:,::2] = mujoco_qpos
    mujoco_phase[:,1::2] = mujoco_qvel


    sim_key = [key for key in simulation_dict.keys() if key.startswith("result__")]

    mujoco_exp = {}
    mujoco_exp["time"] = mujoco_time
    mujoco_exp["qpos"] = mujoco_qpos
    mujoco_exp["qvel"] = mujoco_qvel
    mujoco_exp["qacc"] = mujoco_qacc
    mujoco_exp["line_style"] =(0, (5, 10)) # loosely dashed
    mujoco_exp["color"] = 'black'

    exp_database = {}

    for sim in sim_key:

        exp_dict=simulation_dict[sim]

        if "solution" in exp_dict  and (not args.skip_already_done or not "RMSE_trajectory" in exp_dict ): # add this for not redundancy : and not "RMSE_trajectory" in exp_dict
            

            _, _, _, catalog_repartition, extra_info = xlsindy_component(mode=exp_dict["algoritm"],random_seed=exp_dict["random_seed"],sindy_catalog_len=exp_dict["catalog_len"])

            solution=np.array(exp_dict["solution"])
            #solution=np.array(exp_dict["ideal_solution"])

            model_acceleration_func, valid_model = xlsindy.dynamics_modeling.generate_acceleration_function(solution,catalog_repartition, symbols_matrix, time_sym,lambdify_module="numpy")
            if not valid_model:
                print("-----------------------------------------------The model is not valid-------------------------------------------------------------------------------------------------------------------------------------------------------------------")
                
            model_dynamics_system = xlsindy.dynamics_modeling.dynamics_function(model_acceleration_func,forces_wrapper(forces_function)) 
            try:
                time_values, phase_values = xlsindy.dynamics_modeling.run_rk45_integration(model_dynamics_system, extra_info["initial_condition"], args.max_time, max_step=0.1)
            except Exception as e:
                print(f"An error occurred on the RK45 integration: {e}")
                continue
            theta_values = phase_values[:, ::2]
            velocity_values = phase_values[:, 1::2]

            acceleration_values = np.gradient(velocity_values, time_values, axis=0, edge_order=1)

            exp_database[sim] = {}
            ## Add here the register in the simulation dictionnary the performance of it.
            if np.max(time_values) == args.max_time: # Means that it is successful
                
                mujoco_phase_interp = np.zeros(phase_values.shape)

                for i in range(mujoco_phase_interp.shape[1]):

                    mujoco_phase_interp[:,i] = np.interp(time_values,mujoco_time,mujoco_phase[:,i])

                RMSE_trajectory = xlsindy.result_formatting.relative_mse(phase_values,mujoco_phase_interp)
                exp_dict["RMSE_trajectory"]=RMSE_trajectory
                exp_database[sim]["RMSE"]=RMSE_trajectory
                print("RMSE trajectory :",RMSE_trajectory)


            
            exp_database[sim]["time"] = time_values
            exp_database[sim]["qpos"] = theta_values
            exp_database[sim]["qvel"] = velocity_values
            exp_database[sim]["qacc"] = acceleration_values

            #color info
            exp_database[sim]["noise_level"] = exp_dict["noise_level"]
            exp_database[sim]["algoritm"] = exp_dict["algoritm"]
            exp_database[sim]["optimization_function"] = exp_dict["optimization_function"]
            exp_database[sim]["line_style"] = '-'

    generate_colors_for_experiments(exp_database)

    unique_combos = sorted(list(set((exp["algoritm"], exp["optimization_function"]) for exp in exp_database.values())))

    reverse_unique_combos = {combo:i for i,combo in enumerate(unique_combos)}

    exp_database = dict(sorted(exp_database.items(), key=lambda item: item[1]["noise_level"]))

    exp_database["mujoco"] = mujoco_exp

    simulation_dict = xlsindy.result_formatting.convert_to_strings(simulation_dict)
    print("print model ...")
    with open(args.experiment_file+".json", 'w') as file:
        json.dump(simulation_dict, file, indent=4)

    if args.plot:

        #fig, axs = plt.subplots(3*num_coordinates, 1+len(unique_combos), sharex=True, figsize=(10, 8))
        fig = plt.figure(figsize=(26, 13))
        gs = gridspec.GridSpec(nrows=3*num_coordinates, ncols=2+len(unique_combos), figure=fig,width_ratios=[3,0.14]+[1 for _ in range(len(unique_combos)) ],wspace=0.075,hspace=0.1)
        axs = []
        

        for i in range(3*num_coordinates):
            if i==0:
                
                axs+=[fig.add_subplot(gs[i,0])]
            else:
                axs+=[fig.add_subplot(gs[i,0],sharex=axs[0])]

            if i<3*num_coordinates-1:
                axs[i].tick_params(labelbottom=False)
        
        axs2 = np.empty((3*num_coordinates,len(unique_combos)),dtype=object)

        for i in range(3*num_coordinates):

            for j in range(len(unique_combos)):

                if i==0:
                    share_x=None
                else:
                    sharex=axs2[0,j]

                if j==0:
                    share_y=None
                else:
                    share_y=axs2[i,0]

                axs2[i,j] = fig.add_subplot(gs[i,j+2],sharex=share_x,sharey=share_y)
                axs2[i,j].grid(axis="y")
                if i<3*num_coordinates-1:
                    axs2[i,j].tick_params(labelbottom=False)
                if j>0:
                    axs2[i,j].tick_params(labelleft=False)
        
        # Plot each time series
        for exp in exp_database:

            for i in range(num_coordinates):

                if exp=="mujoco" and i==0:
                    axs[i].plot(exp_database[exp]["time"], exp_database[exp]["qpos"][:,i], c=exp_database[exp]["color"],linestyle=exp_database[exp]["line_style"],label="real system")
                else:
                    axs[i].plot(exp_database[exp]["time"], exp_database[exp]["qpos"][:,i], c=exp_database[exp]["color"],linestyle=exp_database[exp]["line_style"])
                axs[num_coordinates+i].plot(exp_database[exp]["time"], exp_database[exp]["qvel"][:,i],  c=exp_database[exp]["color"],linestyle=exp_database[exp]["line_style"]) 

                if exp=="mujoco":
                    auto_zoom_viewport(axs[i], exp_database[exp]["time"], exp_database[exp]["qpos"][:,i])
                    auto_zoom_viewport(axs[num_coordinates+i], exp_database[exp]["time"], exp_database[exp]["qvel"][:,i])
                    auto_zoom_viewport(axs[num_coordinates*2+i], exp_database[exp]["time"], exp_database[exp]["qacc"][:,i])
                else: # dependent plot
                    
                    combo_indice = reverse_unique_combos[(exp_database[exp]["algoritm"], exp_database[exp]["optimization_function"])]

                    mujoco_qpos_interp = np.interp(exp_database[exp]["time"],mujoco_time,mujoco_qpos[:,i])
                    mujoco_qvel_interp = np.interp(exp_database[exp]["time"],mujoco_time,mujoco_qvel[:,i])
                    mujoco_qacc_interp = np.interp(exp_database[exp]["time"],mujoco_time,mujoco_qacc[:,i])
                    if i==0:
                        if "RMSE" in exp_database[exp]:
                            axs2[i,combo_indice].plot(exp_database[exp]["time"], np.abs(exp_database[exp]["qpos"][:,i]-mujoco_qpos_interp), c=exp_database[exp]["color"],linestyle=exp_database[exp]["line_style"],label=f"n:{exp_database[exp]["noise_level"]:.0e} RMSE : {exp_database[exp]["RMSE"]:.1e}")
                        else:
                            axs2[i,combo_indice].plot(exp_database[exp]["time"], np.abs(exp_database[exp]["qpos"][:,i]-mujoco_qpos_interp), c=exp_database[exp]["color"],linestyle=exp_database[exp]["line_style"],label=f"n:{exp_database[exp]["noise_level"]}")
                    else:
                        axs2[i,combo_indice].plot(exp_database[exp]["time"], np.abs(exp_database[exp]["qpos"][:,i]-mujoco_qpos_interp), c=exp_database[exp]["color"],linestyle=exp_database[exp]["line_style"])
                    axs2[num_coordinates+i,combo_indice].plot(exp_database[exp]["time"], np.abs(exp_database[exp]["qvel"][:,i]-mujoco_qvel_interp),  c=exp_database[exp]["color"],linestyle=exp_database[exp]["line_style"]) 
                    axs2[num_coordinates*2+i,combo_indice].plot(exp_database[exp]["time"], np.abs(exp_database[exp]["qacc"][:,i]-mujoco_qacc_interp),  c=exp_database[exp]["color"],linestyle=exp_database[exp]["line_style"]) 



        for i in range(num_coordinates):

            
            axs[i].set_ylabel(f'$q_{{{i}}}$',ha="center",rotation="vertical")
            axs[num_coordinates+i].set_ylabel(f'$\\dot{{q}}_{{{i}}}$',ha="center",rotation="vertical")
            axs[num_coordinates*2+i].set_ylabel(f'$u_{{{i}}}$',ha="center",rotation="vertical")
            axs[num_coordinates*2+i].plot(mujoco_time, force_vector[:,i],  c="red",linestyle="-") #, color='tab:green')

            axs2[i,0].set_ylabel(f'$| q_{{{i}}}- q^i_{{{i}}} |$',ha="center",rotation="vertical")
            axs2[num_coordinates+i,0].set_ylabel(f'$| \\dot{{q}}_{{{i}}} - \\dot{{q^i}}_{{{i}}} |$',ha="center",rotation="vertical")
            axs2[num_coordinates*2+i,0].set_ylabel(f'$| \\ddot{{q}}_{{{i}}} - \\ddot{{q^i}}_{{{i}}} |$',ha="center",rotation="vertical")

            for j in range(len(unique_combos)):

                axs2[i,j].set_yscale("log")
                axs2[num_coordinates+i,j].set_yscale("log")
                axs2[num_coordinates*2+i,j].set_yscale("log")

        for j in range(len(unique_combos)):
            axs2[0,j].xaxis.set_label_position('top')  # Move the xlabel to the top
            axs2[0,j].set_xlabel(f"{unique_combos[j][0]} - {" ".join(unique_combos[j][1].split("_"))}", labelpad=10)  # Top label with padding
            axs2[0,j].legend(loc="lower right", fontsize=8)
            axs2[-1,j].set_xlabel("Time (s)")

        axs[0].legend()
        axs[-1].set_xlabel("Time (s)")
            #axs[3].legend(loc='upper right')

        #plt.tight_layout()
        fig.savefig(f"poster_figure/trajectory_validation.svg", format="svg")
        plt.show()
