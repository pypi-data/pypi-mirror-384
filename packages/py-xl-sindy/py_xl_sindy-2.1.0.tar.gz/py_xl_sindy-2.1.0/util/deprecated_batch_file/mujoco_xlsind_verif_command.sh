# This file summarize all the command to launch mujoco and the xlsindy, to match both curve


# No friction, double pendulum verification (need to change gen and xml)
python mujoco_align.py \
--experiment-folder "mujoco_align_data/double_pendulum_pm" \
--max-time 30 \
--no-real_mujoco_time \
--forces-scale-vector 0.3 0.3 \
--forces-period 3 \
--forces-period-shift 0.5 \
--regression \
--force-ideal-solution \
--generate-ideal-path

# Result 
# - Variance 0.137 %

# Friction on the first joint, double pendulum verification (need to change gen and xml)
python mujoco_align.py \
--experiment-folder "mujoco_align_data/double_pendulum_pm" \
--max-time 30 \
--no-real_mujoco_time \
--forces-scale-vector 1 0.3 \
--forces-period 3 \
--forces-period-shift 0.5 \
--regression \
--force-ideal-solution \
--generate-ideal-path

# Result 
# - Variance 0.233 %

# Friction on both joint, double pendulum verification (need to change gen and xml)
python mujoco_align.py \
--experiment-folder "mujoco_align_data/double_pendulum_pm" \
--max-time 30 \
--no-real_mujoco_time \
--forces-scale-vector 2 3 \
--forces-period 3 \
--forces-period-shift 0.5 \
--regression \
--force-ideal-solution \
--generate-ideal-path

# Result 
# - Variance 6.2 % -> means error
# - Variance 0.01 % -> No error anymore but something is strange in euler_lagrange.py l112. Solved

# No friction, cartpole [0,0]
python mujoco_align.py \
--experiment-folder "mujoco_align_data/cart_pole" \
--max-time 30 \
--no-real_mujoco_time \
--forces-scale-vector 0.3 0.3 \
--forces-period 3 \
--forces-period-shift 0.5 \
--regression \
--force-ideal-solution \
--generate-ideal-path

# Result
# - Variance 0.05%

# Friction on first joint, cartpole [0.8,0]
python mujoco_align.py \
--experiment-folder "mujoco_align_data/cart_pole" \
--max-time 30 \
--no-real_mujoco_time \
--forces-scale-vector 2 1 \
--forces-period 3 \
--forces-period-shift 0.5 \
--regression \
--force-ideal-solution \
--generate-ideal-path

# Result
# - Variance 0.023 %

# Friction on both joint, cartpole [0.8,0.3]
python mujoco_align.py \
--experiment-folder "mujoco_align_data/cart_pole" \
--max-time 30 \
--no-real_mujoco_time \
--forces-scale-vector 4 5 \
--forces-period 3 \
--forces-period-shift 0.5 \
--regression \
--force-ideal-solution 

# Result
# - Variance 0.066 %

# No Friction, cartpole double pendulum [0.,0.,0.]
python mujoco_align.py \
--experiment-folder "mujoco_align_data/cart_pole_double" \
--max-time 2 \
--no-real_mujoco_time \
--forces-scale-vector 0.2 0.2 0.3 \
--forces-period 3 \
--forces-period-shift 0.5 \
--regression \
--force-ideal-solution \
--generate-ideal-path
# Result
# - Variance 0.061 %


# Friction on three joint, cartpole double pendulum [0.5,0.8,0.2]
python mujoco_align.py \
--experiment-folder "mujoco_align_data/cart_pole_double" \
--max-time 30 \
--no-real_mujoco_time \
--forces-scale-vector 3 6 8 \
--forces-period 3 \
--forces-period-shift 0.5 \
--regression \
--force-ideal-solution \
--generate-ideal-path
# Result
# - Variance 0.023%