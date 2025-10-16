"""
The first script of example for fitting XlSindy on double pendulum.

This script is actually broken right now... Comparison are totally non sense. I will try to fix it later.

DEPRECATED: some function have been deleted.
"""

import numpy as np
from xlsindy.simulation import *
import matplotlib.pyplot as plt
import sympy as sp

# Setup Problem Parameters
use_regression = True

# Initial parameters
link1_length = 1.0
link2_length = 1.0
mass1 = 0.8
mass2 = 0.8
initial_conditions = np.array([[2, 0], [0, 0]])  # Initial state matrix (k,2)
friction_forces = [-1.4, -1.2]
max_force_span = [15.8, 4.5]
time_period = 1.0
time_shift = 0.2
scale_factor = 10  # Base multiplier for scaling
num_periods = 5  # Number of periods for the simulation

# Symbols and symbolic matrix generation
time_sym = sp.symbols("t")
num_coordinates = 2
symbols_matrix = generate_symbolic_matrix(num_coordinates, time_sym)

# Assign ideal model variables
theta1 = symbols_matrix[1, 0]
theta1_d = symbols_matrix[2, 0]
theta1_dd = symbols_matrix[3, 0]
theta2 = symbols_matrix[1, 1]
theta2_d = symbols_matrix[2, 1]
theta2_dd = symbols_matrix[3, 1]

m1, l1, m2, l2, g = sp.symbols("m1 l1 m2 l2 g")
total_length = link1_length + link2_length
substitutions = {
    "g": 9.81,
    "l1": link1_length,
    "m1": mass1,
    "l2": link2_length,
    "m2": mass2,
}

# Lagrangian (L)
L = (
    0.5 * (m1 + m2) * l1**2 * theta1_d**2
    + 0.5 * m2 * l2**2 * theta2_d**2
    + m2 * l1 * l2 * theta1_d * theta2_d * sp.cos(theta1 - theta2)
    + (m1 + m2) * g * l1 * sp.cos(theta1)
    + m2 * g * l2 * sp.cos(theta2)
)

# Catalog creation
degree_function = 4
model_power = 2

# Function catalogs for modeling
function_catalog_1 = [lambda x: symbols_matrix[2, x]]
function_catalog_2 = [
    lambda x: sp.sin(symbols_matrix[1, x]),
    lambda x: sp.cos(symbols_matrix[1, x]),
]

catalog_part1 = np.array(generate_full_catalog(function_catalog_1, num_coordinates, 2))
catalog_part2 = np.array(generate_full_catalog(function_catalog_2, num_coordinates, 2))
cross_catalog = np.outer(catalog_part2, catalog_part1)
full_catalog = np.concatenate((cross_catalog.flatten(), catalog_part1, catalog_part2))

# Generate solution vector
ideal_solution_vector = create_solution_vector(
    sp.expand_trig(L.subs(substitutions)), full_catalog, friction_terms=friction_forces
)
catalog_length = len(full_catalog)

# Simulation parameters
simulation_end_time = time_period * catalog_length / num_periods
print(f"Simulation time: {simulation_end_time}, Catalog length: {catalog_length}")

# External forces
external_force_func = optimized_force_generator(
    num_coordinates,
    max_force_span,
    simulation_end_time,
    time_period,
    time_shift,
    augmentations=15,
)

# Simulation setup
cutoff = 5
acceleration_func, _ = generate_acceleration_function(
    L,
    symbols_matrix,
    time_sym,
    substitution_dict=substitutions,
    fluid_forces=friction_forces,
)
dynamics_system = dynamics_function(acceleration_func, external_force_func)

# Integration and simulation
time_values, phase_values = run_rk45_integration(
    dynamics_system, initial_conditions, simulation_end_time, max_step=0.01
)
theta_values = phase_values[:, ::2]
velocity_values = phase_values[:, 1::2]
acceleration_values = np.gradient(
    phase_values[:, 1::2], time_values, axis=0, edge_order=2
)

# Regression
num_time_points = len(time_values)
subsample_rate = num_time_points // (scale_factor * catalog_length)
ideal_model_expression = create_solution_expression(
    ideal_solution_vector[:, 0], full_catalog, friction_count=len(friction_forces)
)

print("Ideal Model:", ideal_model_expression)

solution, experiment_matrix, subsample_time_values, _ = execute_regression(
    time_values,
    theta_values,
    time_sym,
    symbols_matrix,
    full_catalog,
    external_force_func,
    subsample_rate=subsample_rate,
    velocity_values=velocity_values,
    acceleration_values=acceleration_values,
    use_regression=use_regression,
    hard_threshold=3e-3,
)

if use_regression:
    error = np.linalg.norm(
        solution / np.max(solution)
        - ideal_solution_vector / np.max(ideal_solution_vector)
    ) / np.linalg.norm(ideal_solution_vector / np.max(ideal_solution_vector))
    print(f"Solution Error: {error}")
    print("Sparsity:", np.sum(np.where(np.abs(solution) > 0, 1, 0)))

# Generate plots
fig, axs = plt.subplots(3, 4)
fig.suptitle("Double Pendulum Experiment Results")

axs[0, 0].set_title("q0")
axs[1, 0].set_title("q1")
axs[0, 0].plot(time_values, theta_values[:, 0])
axs[1, 0].plot(time_values, theta_values[:, 1])

## This is totally wrong... Reformulating made me forgot some stuff

if solution is not None:
    dynamics_system_validated = dynamics_function(
        acceleration_func, external_force_func
    )
    validated_time_values, validated_theta_values = run_rk45_integration(
        dynamics_system_validated,
        initial_conditions,
        simulation_end_time,
        max_step=0.05,
    )
    axs[0, 0].plot(
        validated_time_values,
        validated_theta_values[:, 0],
        "--",
        label="Model - Reg. Classic",
    )
    axs[1, 0].plot(
        validated_time_values,
        validated_theta_values[:, 2],
        "--",
        label="Model - Reg. Classic",
    )

axs[0, 1].set_title("q0_d")
axs[1, 1].set_title("q1_d")
axs[0, 1].plot(time_values, velocity_values[:, 0])
axs[1, 1].plot(time_values, velocity_values[:, 1])

# Display phase and regression error
axs[2, 0].set_title("Regression Error")
force_vector = calculate_forces_vector(external_force_func, subsample_time_values)
axs[2, 0].plot(
    np.repeat(subsample_time_values, num_coordinates) * 2,
    (experiment_matrix @ ideal_solution_vector - force_vector),
    label="Ideal Solution",
)

if use_regression:
    axs[2, 0].plot(
        np.repeat(subsample_time_values, num_coordinates) * 2,
        (experiment_matrix @ solution - force_vector),
        label="Solution",
    )

axs[2, 1].set_title("Model Comparison")
bar_height_ideal = np.abs(solution) / np.max(np.abs(solution))
axs[2, 1].bar(
    np.arange(len(ideal_solution_vector)),
    bar_height_ideal[:, 0],
    width=1,
    label="True Model",
)

if use_regression:
    bar_height_found = np.abs(solution) / np.max(np.abs(solution))
    axs[2, 1].bar(
        np.arange(len(ideal_solution_vector)),
        bar_height_found[:, 0],
        width=0.5,
        label="Model Found",
    )

axs[2, 1].legend()

plt.show()
