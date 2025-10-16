python mujoco_ideal_comparison.py \
    --random-seed 12 14 \
    --experiment-folder "mujoco_align_data/cart_pole" \
    --max-time 20 \
    --forces-scale-vector 3.04 1.64 \
    --initial-position 2 1 4 5 \
    --forces-period 3 \
    --forces-period-shift 0.5

python mujoco_ideal_comparison.py \
    --random-seed 12 14 \
    --experiment-folder "mujoco_align_data/double_pendulum_pm" \
    --max-time 20 \
    --forces-scale-vector 0.0 0.0 \
    --initial-position 0.2 0 0.2 0 \
    --forces-period 3 \
    --forces-period-shift 0.5

python mujoco_ideal_comparison.py \
    --random-seed 12 14 \
    --experiment-folder "mujoco_align_data/cart_pole_double" \
    --max-time 20 \
    --forces-scale-vector 3.04 1.64 3 \
    --initial-position 2 1 4 5 6 7 \
    --forces-period 3 \
    --forces-period-shift 0.5