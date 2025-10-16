""" 
This script execute a python file for every file in result.
It is mainly used to execute :
- align_data.py
- exploration_metric.py
"""

import subprocess
from concurrent.futures import ThreadPoolExecutor

import os
import glob

from dataclasses import dataclass
from dataclasses import field
from typing import List
import tyro


@dataclass
class Args:
    script: str = "align_data"
    """the script to launch : can be from multiple type"""
    script_args: List[str] = field(default_factory=lambda: [])
    """the script argument to be passed (check the script to know order)"""
    random_seed: int = 10
    """the random seed for generating the noise in the alignement"""


def run_command(cmd):
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.stdout, result.stderr


if __name__ == "__main__":

    args = tyro.cli(Args)

    if args.script == "align_data":

        def command_generator(filepath, i):

            return [
                "python",
                "align_data.py",
                "--experiment-file",
                filepath,
                "--optimization-function",
                args.script_args[0],
                "--algorithm",
                args.script_args[1],
                "--noise-level",
                str(args.script_args[2]),
                "--random-seed",
                str(args.random_seed),
            ]

    if args.script == "exploration_metric":

        def command_generator(filepath, i):

            return [
                "python",
                "exploration_metric.py",
                "--experiment-file",
                filepath,
            ]

    if args.script == "validation_trajectory":

        def command_generator(filepath, i):

            return [
                "python",
                "validation_trajectory.py",
                "--experiment-file",
                filepath,
                "--max-time",
                str(args.script_args[0]),
                "--random-seed",
                str(args.random_seed),
            ]

    commands = []

    # Loop through all .json files in the "result" folder
    for i, json_file in enumerate(glob.glob("result/*.json"), start=0):
        # Remove the .json extension from the file path
        base_filepath = os.path.splitext(json_file)[0]
        # print(base_filepath)
        commands.append(command_generator(base_filepath, i))

    # num_threads = max(1, 1*(os.cpu_count() // 10))
    num_threads = 10

    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = [executor.submit(run_command, cmd) for cmd in commands]
        for future in futures:
            stdout, stderr = future.result()
            if stdout:
                print("Output:", stdout)
            if stderr:
                print("Error:", stderr)
