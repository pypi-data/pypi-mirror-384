# This scripts runs a series of tests that should match the result in single_test_result_alignment folder.


# Double pendulum pm
python single_test.py \
    --random-seed 12 14 \
    --experiment-folder "mujoco_align_data/double_pendulum_pm" \
    --max-time 120 \
    --forces-scale-vector 3 3 \
    --forces-period 3 \
    --forces-period-shift 0.5 \
    --sample-number 4000 \
    --optimization-function "hard_threshold_sparse_regression" \
    --algorithm "xlsindy" \
    --noise-level 0.0 \
    --no-implicit-regression \
    --no-mujoco-generation

python single_test.py \
    --random-seed 12 14 \
    --experiment-folder "mujoco_align_data/double_pendulum_pm" \
    --max-time 120 \
    --forces-scale-vector 3 3 \
    --forces-period 3 \
    --forces-period-shift 0.5 \
    --sample-number 4000 \
    --optimization-function "hard_threshold_sparse_regression" \
    --algorithm "xlsindy" \
    --noise-level 0.0 \
    --no-implicit-regression 

python single_test.py \
    --random-seed 12 14 \
    --experiment-folder "mujoco_align_data/double_pendulum_pm" \
    --max-time 120 \
    --forces-scale-vector 3 3 \
    --forces-period 3 \
    --forces-period-shift 0.5 \
    --sample-number 4000 \
    --optimization-function "hard_threshold_sparse_regression" \
    --algorithm "sindy" \
    --noise-level 0.0 \
    --no-implicit-regression \
    --no-mujoco-generation

python single_test.py \
    --random-seed 12 14 \
    --experiment-folder "mujoco_align_data/double_pendulum_pm" \
    --max-time 120 \
    --forces-scale-vector 3 3 \
    --forces-period 3 \
    --forces-period-shift 0.5 \
    --sample-number 4000 \
    --optimization-function "hard_threshold_sparse_regression" \
    --algorithm "sindy" \
    --noise-level 0.0 \
    --no-implicit-regression

python single_test.py \
    --random-seed 12 14 \
    --experiment-folder "mujoco_align_data/double_pendulum_pm" \
    --max-time 120 \
    --forces-scale-vector 3 3 \
    --forces-period 3 \
    --forces-period-shift 0.5 \
    --sample-number 4000 \
    --optimization-function "lasso_regression" \
    --algorithm "xlsindy" \
    --noise-level 0.0 \
    --no-implicit-regression \
    --no-mujoco-generation

python single_test.py \
    --random-seed 12 14 \
    --experiment-folder "mujoco_align_data/double_pendulum_pm" \
    --max-time 120 \
    --forces-scale-vector 3 3 \
    --forces-period 3 \
    --forces-period-shift 0.5 \
    --sample-number 4000 \
    --optimization-function "lasso_regression" \
    --algorithm "xlsindy" \
    --noise-level 0.0 \
    --no-implicit-regression 

python single_test.py \
    --random-seed 12 14 \
    --experiment-folder "mujoco_align_data/double_pendulum_pm" \
    --max-time 120 \
    --forces-scale-vector 3 3 \
    --forces-period 3 \
    --forces-period-shift 0.5 \
    --sample-number 4000 \
    --optimization-function "lasso_regression" \
    --algorithm "sindy" \
    --noise-level 0.0 \
    --no-implicit-regression \
    --no-mujoco-generation

python single_test.py \
    --random-seed 12 14 \
    --experiment-folder "mujoco_align_data/double_pendulum_pm" \
    --max-time 120 \
    --forces-scale-vector 3 3 \
    --forces-period 3 \
    --forces-period-shift 0.5 \
    --sample-number 4000 \
    --optimization-function "lasso_regression" \
    --algorithm "sindy" \
    --noise-level 0.0 \
    --no-implicit-regression

# Cartpole 
python single_test.py \
    --random-seed 12 14 \
    --experiment-folder "mujoco_align_data/cart_pole" \
    --max-time 120 \
    --forces-scale-vector 3 3 \
    --forces-period 3 \
    --forces-period-shift 0.5 \
    --sample-number 4000 \
    --optimization-function "hard_threshold_sparse_regression" \
    --algorithm "xlsindy" \
    --noise-level 0.0 \
    --no-implicit-regression \
    --no-mujoco-generation

python single_test.py \
    --random-seed 12 14 \
    --experiment-folder "mujoco_align_data/cart_pole" \
    --max-time 120 \
    --forces-scale-vector 3 3 \
    --forces-period 3 \
    --forces-period-shift 0.5 \
    --sample-number 4000 \
    --optimization-function "hard_threshold_sparse_regression" \
    --algorithm "xlsindy" \
    --noise-level 0.0 \
    --no-implicit-regression 

python single_test.py \
    --random-seed 12 14 \
    --experiment-folder "mujoco_align_data/cart_pole" \
    --max-time 120 \
    --forces-scale-vector 3 3 \
    --forces-period 3 \
    --forces-period-shift 0.5 \
    --sample-number 4000 \
    --optimization-function "hard_threshold_sparse_regression" \
    --algorithm "sindy" \
    --noise-level 0.0 \
    --no-implicit-regression \
    --no-mujoco-generation

python single_test.py \
    --random-seed 12 14 \
    --experiment-folder "mujoco_align_data/cart_pole" \
    --max-time 120 \
    --forces-scale-vector 3 3 \
    --forces-period 3 \
    --forces-period-shift 0.5 \
    --sample-number 4000 \
    --optimization-function "hard_threshold_sparse_regression" \
    --algorithm "sindy" \
    --noise-level 0.0 \
    --no-implicit-regression 

python single_test.py \
    --random-seed 12 14 \
    --experiment-folder "mujoco_align_data/cart_pole" \
    --max-time 120 \
    --forces-scale-vector 3 3 \
    --forces-period 3 \
    --forces-period-shift 0.5 \
    --sample-number 4000 \
    --optimization-function "lasso_regression" \
    --algorithm "xlsindy" \
    --noise-level 0.0 \
    --no-implicit-regression \
    --no-mujoco-generation

python single_test.py \
    --random-seed 12 14 \
    --experiment-folder "mujoco_align_data/cart_pole" \
    --max-time 120 \
    --forces-scale-vector 3 3 \
    --forces-period 3 \
    --forces-period-shift 0.5 \
    --sample-number 4000 \
    --optimization-function "lasso_regression" \
    --algorithm "xlsindy" \
    --noise-level 0.0 \
    --no-implicit-regression 

python single_test.py \
    --random-seed 12 14 \
    --experiment-folder "mujoco_align_data/cart_pole" \
    --max-time 120 \
    --forces-scale-vector 3 3 \
    --forces-period 3 \
    --forces-period-shift 0.5 \
    --sample-number 4000 \
    --optimization-function "lasso_regression" \
    --algorithm "sindy" \
    --noise-level 0.0 \
    --no-implicit-regression \
    --no-mujoco-generation

python single_test.py \
    --random-seed 12 14 \
    --experiment-folder "mujoco_align_data/cart_pole" \
    --max-time 120 \
    --forces-scale-vector 3 3 \
    --forces-period 3 \
    --forces-period-shift 0.5 \
    --sample-number 4000 \
    --optimization-function "lasso_regression" \
    --algorithm "sindy" \
    --noise-level 0.0 \
    --no-implicit-regression 

# Cartpole double
python single_test.py \
    --random-seed 12 14 \
    --experiment-folder "mujoco_align_data/cart_pole_double" \
    --max-time 120 \
    --forces-scale-vector 3 3 3 \
    --forces-period 3 \
    --forces-period-shift 0.5 \
    --sample-number 4000 \
    --optimization-function "hard_threshold_sparse_regression" \
    --algorithm "xlsindy" \
    --noise-level 0.0 \
    --no-implicit-regression \
    --no-mujoco-generation

python single_test.py \
    --random-seed 12 14 \
    --experiment-folder "mujoco_align_data/cart_pole_double" \
    --max-time 120 \
    --forces-scale-vector 3 3 3 \
    --forces-period 3 \
    --forces-period-shift 0.5 \
    --sample-number 4000 \
    --optimization-function "hard_threshold_sparse_regression" \
    --algorithm "xlsindy" \
    --noise-level 0.0 \
    --no-implicit-regression 

python single_test.py \
    --random-seed 12 14 \
    --experiment-folder "mujoco_align_data/cart_pole_double" \
    --max-time 120 \
    --forces-scale-vector 3 3 3 \
    --forces-period 3 \
    --forces-period-shift 0.5 \
    --sample-number 4000 \
    --optimization-function "hard_threshold_sparse_regression" \
    --algorithm "sindy" \
    --noise-level 0.0 \
    --no-implicit-regression \
    --no-mujoco-generation

python single_test.py \
    --random-seed 12 14 \
    --experiment-folder "mujoco_align_data/cart_pole_double" \
    --max-time 120 \
    --forces-scale-vector 3 3 3 \
    --forces-period 3 \
    --forces-period-shift 0.5 \
    --sample-number 4000 \
    --optimization-function "hard_threshold_sparse_regression" \
    --algorithm "sindy" \
    --noise-level 0.0 \
    --no-implicit-regression 

python single_test.py \
    --random-seed 12 14 \
    --experiment-folder "mujoco_align_data/cart_pole_double" \
    --max-time 120 \
    --forces-scale-vector 3 3 3 \
    --forces-period 3 \
    --forces-period-shift 0.5 \
    --sample-number 4000 \
    --optimization-function "lasso_regression" \
    --algorithm "xlsindy" \
    --noise-level 0.0 \
    --no-implicit-regression \
    --no-mujoco-generation

python single_test.py \
    --random-seed 12 14 \
    --experiment-folder "mujoco_align_data/cart_pole_double" \
    --max-time 120 \
    --forces-scale-vector 3 3 3 \
    --forces-period 3 \
    --forces-period-shift 0.5 \
    --sample-number 4000 \
    --optimization-function "lasso_regression" \
    --algorithm "xlsindy" \
    --noise-level 0.0 \
    --no-implicit-regression 

python single_test.py \
    --random-seed 12 14 \
    --experiment-folder "mujoco_align_data/cart_pole_double" \
    --max-time 120 \
    --forces-scale-vector 3 3 3 \
    --forces-period 3 \
    --forces-period-shift 0.5 \
    --sample-number 4000 \
    --optimization-function "lasso_regression" \
    --algorithm "sindy" \
    --noise-level 0.0 \
    --no-implicit-regression \
    --no-mujoco-generation

python single_test.py \
    --random-seed 12 14 \
    --experiment-folder "mujoco_align_data/cart_pole_double" \
    --max-time 120 \
    --forces-scale-vector 3 3 3 \
    --forces-period 3 \
    --forces-period-shift 0.5 \
    --sample-number 4000 \
    --optimization-function "lasso_regression" \
    --algorithm "sindy" \
    --noise-level 0.0 \
    --no-implicit-regression 