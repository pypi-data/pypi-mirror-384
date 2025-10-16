""" 
This scripts only generate data from Mujoco, it is the first step between batch regression, comparison of algorithm and regresion technics
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
import cv2

import numpy as np
import xlsindy

import matplotlib.pyplot as plt

import xlsindy.result_formatting

import time

# loggin purpose
from datetime import datetime
import json


@dataclass
class Args:
    experiment_folder: str = "None"
    """the folder where the experiment data is stored : the mujoco environment.xml file and the xlsindy_gen.py script"""
    max_time: float = 10.0
    """the maximum time for the simulation"""
    forces_scale_vector: List[float] = field(default_factory=lambda: [])
    """the different scale for the forces vector to be applied, this can mimic an action mask over the system if some entry are 0"""
    forces_period: float = 3.0
    """the period for the forces function"""
    forces_period_shift: float = 0.5
    """the shift for the period of the forces function"""
    random_seed: List[int] = field(default_factory=lambda: [2])
    """the random seed of the experiment (only used for force function)"""
    sample_number: int = 1000
    """the number of sample for the experiment (ten times the lenght of the catalog works well)"""
    mujoco_record: bool = False
    """if true, render the scene"""


if __name__ == "__main__":

    #os.environ["MUJOCO_GL"] = "egl"

    args = tyro.cli(Args)

    simulation_dict = (
        {}
    )  # the simulation dictionnary storing everything about the simulation
    # print(args)
    simulation_dict["input"] = {}
    simulation_dict["input"]["forces_scale_vector"] = args.forces_scale_vector
    simulation_dict["input"]["max_time"] = args.max_time
    simulation_dict["input"]["forces_period"] = args.forces_period
    simulation_dict["input"]["forces_period_shift"] = args.forces_period_shift
    simulation_dict["input"]["experiment_folder"] = args.experiment_folder.split("/")[
        -1
    ]
    simulation_dict["input"]["sample_number"] = args.sample_number
    simulation_dict["input"]["random_seed"] = args.random_seed

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
            forces_wrapper = xlsindy_gen.forces_wrapper
        except AttributeError:
            forces_wrapper = None

        num_coordinates, time_sym, symbols_matrix, full_catalog, extra_info = (
            xlsindy_component()
        )

        simulation_dict["environment"] = {}
        simulation_dict["environment"]["coordinate_number"] = num_coordinates
        # simulation_dict["environment"]["extra_info"]=extra_info # maybe not necessary ?

        # Mujoco environment path
        mujoco_xml = os.path.join(folder_path, "environment.xml")

    # Random controller initialisation. This is the only random place of the code Everything else is deterministic (except if non deterministic solver is used)
    forces_function = xlsindy.dynamics_modeling.optimized_force_generator(
        component_count=num_coordinates,
        scale_vector=args.forces_scale_vector,
        time_end=args.max_time,
        period=args.forces_period,
        period_shift=args.forces_period_shift,
        augmentations=40,
        random_seed=args.random_seed,
    )

    # initialize Mujoco environment and controller

    mujoco_model = mujoco.MjModel.from_xml_path(mujoco_xml)
    mujoco_data = mujoco.MjData(mujoco_model)

    mujoco_time = []
    mujoco_qpos = []
    mujoco_qvel = []
    mujoco_qacc = []
    force_vector = []

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

    # Viewer of the experiment

    if args.mujoco_record:

        height = 720
        width = 1280

        camera = mujoco.MjvCamera()
        camera.type = mujoco.mjtCamera.mjCAMERA_FIXED
        camera.fixedcamid = 0  # use the first camera defined in the model

        fps = 60
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        video = cv2.VideoWriter("output_2.mp4", fourcc, fps, (width, height))
        C = 0
        with mujoco.Renderer(mujoco_model, height, width) as renderer:

            # Create scene and camera; force use of the first (fixed) camera from the model

            while mujoco_data.time < args.max_time:
                mujoco.mj_step(mujoco_model, mujoco_data)
                # Update scene using the current simulation state and camera view
                if C < mujoco_data.time * fps:
                    renderer.update_scene(mujoco_data, 0)
                    # Convert RGB to BGR for OpenCV and write the frame
                    print("C",C)
                    video.write(cv2.cvtColor(renderer.render(), cv2.COLOR_RGB2BGR))
                    C += 1

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

    mujoco_qpos, mujoco_qvel, mujoco_qacc, force_vector = mujoco_transform(
        mujoco_qpos, mujoco_qvel, mujoco_qacc, force_vector
    )

    raw_sample_number = len(mujoco_time)

    subsample = raw_sample_number // args.sample_number
    start_truncation = 2

    mujoco_time = mujoco_time[start_truncation::subsample]
    mujoco_qpos = mujoco_qpos[start_truncation::subsample]
    mujoco_qvel = mujoco_qvel[start_truncation::subsample]
    mujoco_qacc = mujoco_qacc[start_truncation::subsample]
    force_vector = force_vector[start_truncation::subsample]

    # Logging of every information
    now = datetime.now()
    timestamp = now.strftime("%Y%m%d_%H%M%S")

    filename = f"result/{simulation_dict['input']['experiment_folder']}__{''.join(map(str, args.random_seed))}_{timestamp}"

    np.savez(
        filename + ".npz",
        array1=mujoco_time,
        array2=mujoco_qpos,
        array3=mujoco_qvel,
        array4=mujoco_qacc,
        array5=force_vector,
    )

    simulation_dict = xlsindy.result_formatting.convert_to_strings(simulation_dict)

    with open(filename + ".json", "w") as file:
        json.dump(simulation_dict, file, indent=4)

        print(" Simulation data saved to", filename + ".json")
