"""
This script was only made in the purpose to develop parallel environment.
The goal is to run highly parallel environment step.
"""

import numpy as np
import xlsindy

# from xlsindy.simulation import *
import matplotlib.pyplot as plt
import sympy as sp
from jax import jit
from jax import vmap
import time

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
simulation_end_time = 60.0  # only for jax speedup
time_shift = 0.2
scale_factor = 10  # Base multiplier for scaling
num_periods = 5  # Number of periods for the simulation

# Symbols and symbolic matrix generation
time_sym = sp.symbols("t")
num_coordinates = 2
symbols_matrix = xlsindy.symbolic_util.generate_symbolic_matrix(num_coordinates, time_sym)

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


# Simulation parameters

print(f"Simulation time: {simulation_end_time}")

# External forces

# Benchmark settings

sample = 3000

# Numpy acceleration function

acceleration_func, _ = xlsindy.euler_lagrange.generate_acceleration_function(
    L,
    symbols_matrix,
    time_sym,
    substitution_dict=substitutions,
    fluid_forces=friction_forces,
    lambdify_module="numpy",
)

ts = []

for i in range(sample):
    random_vec = np.random.random(symbols_matrix.shape) * 5

    start = time.perf_counter()
    acceleration_func(random_vec)
    end = time.perf_counter()
    if i > 10:
        ts.append(end - start)

ts = np.array(ts)
print(f"Execution time cpu accel: {ts.mean()*1000:.6f} ms")

## Jax acceleration function, high parallel
parralel_batch = 100  # seems to be capped at 10 000

# Result
# 10 000 : 0.000026 ms
# 20 000 : 0.000019 ms
# 50 000 : 0.000011 ms
# 70 000 : 0.000017 ms
# 100 000 : 0.000 010 ms

acceleration_func, _ = xlsindy.euler_lagrange.generate_acceleration_function(
    L,
    symbols_matrix,
    time_sym,
    substitution_dict=substitutions,
    fluid_forces=friction_forces,
    lambdify_module="jax",
)

acceleration_func = vmap(acceleration_func, in_axes=(2), out_axes=1)

acceleration_func = jit(acceleration_func, backend="gpu")
ts = []

for i in range(sample):
    random_vec = np.random.random(symbols_matrix.shape + (parralel_batch,)) * 5

    start = time.perf_counter()
    acceleration_func(random_vec)
    end = time.perf_counter()
    if i > 10:
        ts.append(end - start)

ts = np.array(ts)
print(
    f"Execution time jax accel: {ts.mean()*1000:.6f} ms relative sequential: {ts.mean()*1000000000/parralel_batch:.3f} ms"
)
print(
    f"Execution time jax accel: {ts.min()*1000:.6f} ms relative sequential: {ts.min()*1000000000/parralel_batch:.3f} ms"
)

# Jax dynamic function, high parallel

acceleration_func, _ = xlsindy.euler_lagrange.generate_acceleration_function(
    L,
    symbols_matrix,
    time_sym,
    substitution_dict=substitutions,
    fluid_forces=friction_forces,
    lambdify_module="jax",
)

dyn_function = xlsindy.dynamics_modeling.dynamics_function_RK4_env(acceleration_func)

dyn_function = vmap(dyn_function, in_axes=(1, 1), out_axes=1)

dyn_function = jit(dyn_function, backend="gpu")
ts = []

for i in range(sample):
    random_vec = (
        np.random.random((symbols_matrix.shape[1] * 2,) + (parralel_batch,)) * 5
    )  # generate a batch of ([q0,q0_d,...,qn,qn_d],...) vector
    random_forces = (
        np.random.random((symbols_matrix.shape[1],) + (parralel_batch,)) * 5
    )  # generate a batch of forces ([f0,...,fn],...) vector

    start = time.perf_counter()
    dyn_function(random_vec, random_forces)
    end = time.perf_counter()

    if i > 10:
        ts.append(end - start)

ts = np.array(ts)
print(
    f"Execution time dyn_function: {ts.mean()*1000:.6f} ms relative sequential: {ts.mean()*1000/parralel_batch:.6f} ms"
)
print(
    f"min time dyn_function: {ts.min()*1000:.6f} ms relative sequential: {ts.min()*1000/parralel_batch:.6f} ms"
)

# From experiment we can see that on single environment jax is same speed as numpy (and slower on GPU).
