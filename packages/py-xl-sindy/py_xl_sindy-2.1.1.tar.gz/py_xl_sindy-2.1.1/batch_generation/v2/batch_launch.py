import subprocess
from concurrent.futures import ThreadPoolExecutor

from dataclasses import dataclass
from dataclasses import field
from typing import List
import tyro

import os

import numpy as np


@dataclass
class Args:
    experiment_folder: str = "None"
    """the folder where the experiment data is stored : the mujoco environment.xml file and the xlsindy_gen.py script"""
    max_time: float = 20.0
    """the maximum time for the simulation"""
    number_coordinate: int = 0
    """number of coordinate of the simulation"""
    forces_span: List[float] = field(default_factory=lambda: [1, 2])
    """the start and end of the amplitude ramp for experiment (scale random forces amplitude)"""
    number_experiment: int = 1
    """the number of experiment that will be launched on the ramp"""
    mode: str = "align"
    """the mode of the generation, can be "align" or "generate" to only generate data"""
    random_seed: int = 12
    """the random seed of the generation"""
    sample_number: int = 1000
    """the number of sample if generate is choosen (other a function of catalog lenght)"""


# Function to execute a command
def run_command(cmd):
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.stdout, result.stderr

## Actually this function is DEPRECATED, it is not used anymore
def mujoco_align_cmd_creator(exp, max_time, forces_scale, random_seeds):

    return [
        "python",
        "mujoco_align.py",
        "--experiment-folder",
        exp,
        "--max-time",
        str(max_time),
        "--no-real_mujoco_time",
        "--forces-scale-vector",
        *[str(num) for num in forces_scale],
        "--forces-period",
        "3",
        "--forces-period-shift",
        "0.5",
        "--regression",
        "--random-seed",
        *[str(seed) for seed in random_seeds],
    ]


def mujoco_generate_cmd_creator(
    exp, max_time, forces_scale, random_seeds, sample_number
):

    return [
        "python",
        "mujoco_generate_data.py",
        "--experiment-folder",
        exp,
        "--max-time",
        str(max_time),
        "--forces-scale-vector",
        *[str(num) for num in forces_scale],
        "--forces-period",
        "3",
        "--forces-period-shift",
        "0.5",
        "--random-seed",
        *[str(seed) for seed in random_seeds],
        "--sample-number",
        str(sample_number),
    ]


if __name__ == "__main__":

    args = tyro.cli(Args)

    # cli verification
    if args.number_coordinate == "None":
        raise ValueError(
            "You need to specify the number of coordinate of your environment, don't hesitate to invoke --help"
        )
    if len(args.forces_span) != 2:
        raise ValueError(
            "Force span should have only one start and one end (lenght of 2), don't hesitate to invoke --help"
        )
    if args.number_coordinate == 0:
        raise ValueError(
            "Number of coordinate should be non null, don't hesitate to invoke --help"
        )

    commands = []

    rng = np.random.default_rng(args.random_seed)

    for i in range(args.number_experiment):

        forces_vec = rng.random(args.number_coordinate) * (
            i / args.number_experiment * (args.forces_span[1] - args.forces_span[0])
            + args.forces_span[0]
        )

        if args.mode == "align":
            commands += [
                mujoco_align_cmd_creator(
                    args.experiment_folder,
                    args.max_time,
                    forces_vec,
                    [args.random_seed, i],
                )
            ]
        elif args.mode == "generate":
            commands += [
                mujoco_generate_cmd_creator(
                    args.experiment_folder,
                    args.max_time,
                    forces_vec,
                    [args.random_seed, i],
                    args.sample_number,
                )
            ]

    # num_threads = max(1,1*(os.cpu_count() // 10))
    num_threads = 2
    # Execute commands in parallel
    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = [executor.submit(run_command, cmd) for cmd in commands]
        for future in futures:
            stdout, stderr = future.result()
            if stdout:
                print("Output:", stdout)
            if stderr:
                print("Error:", stderr)
