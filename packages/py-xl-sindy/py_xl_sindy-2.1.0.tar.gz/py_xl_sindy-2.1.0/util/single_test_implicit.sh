python single_test.py \
    --random-seed 12 14 \
    --experiment-folder "mujoco_align_data/double_pendulum_pm" \
    --max-time 20 \
    --forces-scale-vector 0 0 \
    --initial-position 0.2 0 0.2 0 \
    --forces-period 3 \
    --forces-period-shift 0.5 \
    --sample-number 3000 \
    --optimization-function "hard_threshold_sparse_regression" \
    --algorithm "xlsindy" \
    --noise-level 0.0 \
    --regression-type "implicit" \
    --no-mujoco-generation

python single_test.py \
    --random-seed 12 14 \
    --experiment-folder "mujoco_align_data/double_pendulum_pm" \
    --max-time 5 \
    --forces-scale-vector 0 0 \
    --initial-position 0.0 0 0.0 0 \
    --forces-period 3 \
    --forces-period-shift 0.5 \
    --sample-number 2000 \
    --optimization-function "hard_threshold_sparse_regression" \
    --algorithm "xlsindy" \
    --noise-level 0.0 \
    --regression-type "implicit" \
    --no-mujoco-generation \
    --batch-number 20 \
    --initial-condition-randomness 1.5

# add the restriction 
python single_test.py \
    --random-seed 12 14 \
    --experiment-folder "mujoco_align_data/double_pendulum_pm" \
    --max-time 5 \
    --forces-scale-vector 0 0 \
    --initial-position 0.0 0 0.0 0 \
    --forces-period 3 \
    --forces-period-shift 0.5 \
    --sample-number 2000 \
    --optimization-function "hard_threshold_sparse_regression" \
    --algorithm "xlsindy" \
    --noise-level 0.0 \
    --regression-type "implicit" \
    --no-mujoco-generation \
    --batch-number 60 \
    --initial-condition-randomness 0.4 \
    --catalog-restriction -1

python single_test.py \
    --random-seed 12 14 \
    --experiment-folder "mujoco_align_data/double_pendulum_pm" \
    --max-time 5 \
    --forces-scale-vector 0 0 \
    --initial-position 0.0 0 0.0 0 \
    --forces-period 3 \
    --forces-period-shift 0.5 \
    --sample-number 2000 \
    --optimization-function "hard_threshold_sparse_regression" \
    --algorithm "xlsindy" \
    --noise-level 0.0 \
    --regression-type "implicit" \
    --no-mujoco-generation \
    --batch-number 60 \
    --initial-condition-randomness 1 \
    --catalog-restriction 0 \
    --implicit-regression-debug

python single_test.py \
    --random-seed 12 14 \
    --experiment-folder "mujoco_align_data/double_pendulum_pm" \
    --max-time 5 \
    --forces-scale-vector 0 0 \
    --initial-position 0.0 0 0.0 0 \
    --forces-period 3 \
    --forces-period-shift 0.5 \
    --sample-number 2000 \
    --optimization-function "hard_threshold_sparse_regression" \
    --algorithm "xlsindy" \
    --noise-level 0.0 \
    --regression-type "implicit" \
    --no-mujoco-generation \
    --batch-number 60 \
    --initial-condition-randomness 1 \
    --catalog-restriction -1 \
    --implicit-regression-debug \
    --implicit-regression-lamba 1e-2

# Work amaxingly well
python single_test.py \
    --random-seed 12 14 \
    --experiment-folder "mujoco_align_data/double_pendulum_pm" \
    --max-time 5 \
    --forces-scale-vector 0 0 \
    --initial-position 0.0 0 0.0 0 \
    --forces-period 3 \
    --forces-period-shift 0.5 \
    --sample-number 2000 \
    --optimization-function "hard_threshold_sparse_regression" \
    --algorithm "xlsindy" \
    --noise-level 0.0 \
    --regression-type "implicit" \
    --no-mujoco-generation \
    --batch-number 60 \
    --initial-condition-randomness 1 \
    --catalog-restriction -1 \
    --no-implicit-regression-debug \
    --implicit-regression-lamba 1e-7

python single_test.py \
    --random-seed 12 15 \
    --experiment-folder "mujoco_align_data/double_pendulum_pm" \
    --max-time 5 \
    --forces-scale-vector 0 0 \
    --initial-position 0.0 0 0.0 0 \
    --forces-period 3 \
    --forces-period-shift 0.5 \
    --sample-number 2000 \
    --optimization-function "hard_threshold_sparse_regression" \
    --algorithm "xlsindy" \
    --noise-level 0.0 \
    --regression-type "implicit" \
    --no-mujoco-generation \
    --batch-number 30 \
    --initial-condition-randomness 1 \
    --catalog-restriction -1 \
    --no-implicit-regression-debug \
    --implicit-regression-lamba 1e-7

# Cart pole 

python single_test.py \
    --random-seed 12 15 \
    --experiment-folder "mujoco_align_data/cart_pole" \
    --max-time 10 \
    --forces-scale-vector 0 0 \
    --initial-position 0.0 0 0.0 0 \
    --forces-period 3 \
    --forces-period-shift 0.5 \
    --sample-number 2000 \
    --optimization-function "hard_threshold_sparse_regression" \
    --algorithm "sindy" \
    --noise-level 0.0 \
    --regression-type "implicit" \
    --no-mujoco-generation \
    --batch-number 20 \
    --initial-condition-randomness 1 4 4 4 \
    --catalog-restriction -1 \
    --no-implicit-regression-debug \
    --implicit-regression-lamba 1e-7

python single_test.py \
    --random-seed 12 15 \
    --experiment-folder "mujoco_align_data/cart_pole" \
    --max-time 5 \
    --forces-scale-vector 0 0 \
    --initial-position 0.0 0 0.0 0 \
    --forces-period 3 \
    --forces-period-shift 0.5 \
    --sample-number 2000 \
    --optimization-function "hard_threshold_sparse_regression" \
    --algorithm "xlsindy" \
    --noise-level 0.0 \
    --regression-type "implicit" \
    --no-mujoco-generation \
    --batch-number 60 \
    --initial-condition-randomness 1 \
    --catalog-restriction -1 \
    --no-implicit-regression-debug \
    --implicit-regression-lamba 1e-7

# Double pendulum cart pole

# work well but slow 
python single_test.py \
    --random-seed 12 15 \
    --experiment-folder "mujoco_align_data/cart_pole_double" \
    --max-time 5 \
    --forces-scale-vector 0 0 0\
    --initial-position 0.0 0 0.0 0 0.0 0\
    --forces-period 3 \
    --forces-period-shift 0.5 \
    --sample-number 1000 \
    --optimization-function "hard_threshold_sparse_regression" \
    --algorithm "xlsindy" \
    --noise-level 0.0 \
    --regression-type "implicit" \
    --no-mujoco-generation \
    --batch-number 60 \
    --initial-condition-randomness 10 10 1 10 1 10 \
    --catalog-restriction -1 \
    --no-implicit-regression-debug \
    --implicit-regression-lamba 1e-7

python single_test.py \
    --random-seed 12 15 \
    --experiment-folder "mujoco_align_data/cart_pole_double" \
    --max-time 5 \
    --forces-scale-vector 0 0 0\
    --initial-position 0.0 0 0.0 0 0.0 0\
    --forces-period 3 \
    --forces-period-shift 0.5 \
    --sample-number 300 \
    --optimization-function "hard_threshold_sparse_regression" \
    --algorithm "xlsindy" \
    --noise-level 0.0 \
    --regression-type "implicit" \
    --no-mujoco-generation \
    --batch-number 60 \
    --initial-condition-randomness 10 10 1 10 1 10 \
    --catalog-restriction -1 \
    --no-implicit-regression-debug \
    --implicit-regression-lamba 1e-7

# enforce minimal catalog

