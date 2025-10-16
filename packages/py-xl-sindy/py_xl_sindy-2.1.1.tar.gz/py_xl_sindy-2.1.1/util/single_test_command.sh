python single_test.py \
    --random-seed 10 \
    --experiment-folder "mujoco_align_data/cart_pole" \
    --max-time 20 \
    --forces-scale-vector 7 4.5 \
    --forces-period 3 \
    --forces-period-shift 0.5 \
    --sample-number 1000 \
    --optimization-function "hard_threshold_sparse_regression" \
    --algorithm "xlsindy" \
    --noise-level 0.0 \
    --no-implicit-regression

python single_test.py \
    --random-seed 10 \
    --experiment-folder "mujoco_align_data/cart_pole" \
    --max-time 20 \
    --forces-scale-vector 15 15 \
    --forces-period 3 \
    --forces-period-shift 0.5 \
    --sample-number 1000 \
    --optimization-function "lasso_regression" \
    --algorithm "xlsindy" \
    --noise-level 0.0 \
    --no-implicit-regression

python single_test.py \
    --random-seed 12 14 \
    --experiment-folder "mujoco_align_data/cart_pole" \
    --max-time 20 \
    --forces-scale-vector 3.049855884605056 1.639574110558981 \
    --forces-period 3 \
    --forces-period-shift 0.5 \
    --sample-number 1000 \
    --optimization-function "hard_threshold_sparse_regression" \
    --algorithm "xlsindy" \
    --noise-level 0.0 \
    --no-implicit-regression
# Compatible with old test catp_pole_1214_20250221_135709.json


# Didn't work as expected
python single_test.py \
    --random-seed 12 \
    --experiment-folder "mujoco_align_data/cart_pole" \
    --max-time 100 \
    --forces-scale-vector 8 8 \
    --forces-period 3 \
    --forces-period-shift 0.5 \
    --sample-number 3000 \
    --optimization-function "hard_threshold_sparse_regression" \
    --algorithm "xlsindy" \
    --noise-level 0.0 \
    --no-implicit-regression

## High residual on second coordinate

# reproduce 1214_20250221_135709
python single_test.py \
    --random-seed 12 14 \
    --experiment-folder "mujoco_align_data/cart_pole" \
    --max-time 20 \
    --forces-scale-vector 3.04 1.64 \
    --forces-period 3 \
    --forces-period-shift 0.5 \
    --sample-number 1000 \
    --optimization-function "hard_threshold_sparse_regression" \
    --algorithm "xlsindy" \
    --noise-level 0.0 \
    --no-implicit-regression

# Eventhough the result are aligned on the past experiement :
# Ideal Residuals :  0.0003005810170027422
# Residuals :  2.6690655610823964e-07
# sparsity difference percentage :  85.71428571428571
# sparsity difference number :  6
# RMSE model comparison :  2.5547514372192657

# We can notice that Ideal residuals are superior to the found residuals.... which is ultimately an issue

python mujoco_ideal_comparison.py \
    --random-seed 12 14 \
    --experiment-folder "mujoco_align_data/cart_pole" \
    --max-time 20 \
    --forces-scale-vector 3.04 1.64 \
    --forces-period 3 \
    --forces-period-shift 0.5

# Force high residual

python single_test.py \
    --random-seed 12 14 \
    --experiment-folder "mujoco_align_data/cart_pole" \
    --max-time 20 \
    --forces-scale-vector 3.04 1.64 \
    --forces-period 3 \
    --forces-period-shift 0.5 \
    --sample-number 1000 \
    --optimization-function "hard_threshold_sparse_regression" \
    --algorithm "xlsindy" \
    --noise-level 4e-5 \
    --no-implicit-regression

python mujoco_ideal_comparison.py \
    --random-seed 12 \
    --experiment-folder "mujoco_align_data/cart_pole" \
    --max-time 100 \
    --forces-scale-vector 8 8 \
    --forces-period 3 \
    --forces-period-shift 0.5

# theorical alignment 

python single_test.py \
    --random-seed 12 14 \
    --experiment-folder "mujoco_align_data/cart_pole" \
    --max-time 20 \
    --forces-scale-vector 3.04 1.64 \
    --forces-period 3 \
    --forces-period-shift 0.5 \
    --sample-number 1000 \
    --optimization-function "hard_threshold_sparse_regression" \
    --algorithm "xlsindy" \
    --noise-level 4e-5 \
    --no-implicit-regression \
    --no-mujoco-generation
# Work better

python single_test.py \
    --random-seed 12 14 \
    --experiment-folder "mujoco_align_data/cart_pole" \
    --max-time 60 \
    --forces-scale-vector 3.04 1.64 \
    --forces-period 3 \
    --forces-period-shift 0.5 \
    --sample-number 1000 \
    --optimization-function "hard_threshold_sparse_regression" \
    --algorithm "xlsindy" \
    --noise-level 4e-5 \
    --no-implicit-regression \
    --no-mujoco-generation

python single_test.py \
    --random-seed 12 14 \
    --experiment-folder "mujoco_align_data/double_pendulum_pm" \
    --max-time 60 \
    --forces-scale-vector 3.04 1.64 \
    --forces-period 3 \
    --forces-period-shift 0.5 \
    --sample-number 1000 \
    --optimization-function "hard_threshold_sparse_regression" \
    --algorithm "xlsindy" \
    --noise-level 0.0 \
    --no-implicit-regression \
    --mujoco-generation

python single_test.py \
    --random-seed 12 14 \
    --experiment-folder "mujoco_align_data/double_pendulum_pm" \
    --max-time 60 \
    --forces-scale-vector 3.04 1.64 \
    --forces-period 3 \
    --forces-period-shift 0.5 \
    --sample-number 1000 \
    --optimization-function "hard_threshold_sparse_regression" \
    --algorithm "sindy" \
    --noise-level 0.0 \
    --no-implicit-regression \
    --no-mujoco-generation

python mujoco_ideal_comparison.py \
    --random-seed 12 \
    --experiment-folder "mujoco_align_data/double_pendulum_pm" \
    --max-time 100 \
    --forces-scale-vector 8 8 \
    --forces-period 3 \
    --forces-period-shift 0.5

## Test alignment 

python mujoco_ideal_comparison.py \
    --random-seed 12 \
    --experiment-folder "mujoco_align_data/double_pendulum_pm" \
    --max-time 20 \
    --forces-scale-vector 5 5 \
    --forces-period 3 \
    --forces-period-shift 0.5

python mujoco_ideal_comparison.py \
    --random-seed 12 \
    --experiment-folder "mujoco_align_data/cart_pole" \
    --max-time 20 \
    --forces-scale-vector 5 5 \
    --forces-period 3 \
    --forces-period-shift 0.5

python mujoco_ideal_comparison.py \
    --random-seed 12 \
    --experiment-folder "mujoco_align_data/cart_pole_double" \
    --max-time 20 \
    --forces-scale-vector 5 5 5 \
    --forces-period 3 \
    --forces-period-shift 0.5

#    Everything is aligned 
# now why it isn't aligned during regression ??

# AHHHHHHHHHHHH 
# I forgot the forces transformer during inferences :clown:

# Total verification

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

# doesn't work memory issue
python single_test.py \
    --random-seed 12 14 \
    --experiment-folder "mujoco_align_data/cart_pole_double" \
    --max-time 120 \
    --forces-scale-vector 3 3 3 \
    --forces-period 3 \
    --forces-period-shift 0.5 \
    --sample-number 1000 \
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
    --sample-number 1000 \
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
    --sample-number 1000 \
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
    --sample-number 1000 \
    --optimization-function "lasso_regression" \
    --algorithm "sindy" \
    --noise-level 0.0 \
    --no-implicit-regression 

# New class paradigm

python single_test.py \
    --random-seed 12 14 \
    --experiment-folder "mujoco_align_data/cart_pole" \
    --max-time 20 \
    --forces-scale-vector 3.049855884605056 1.639574110558981 \
    --forces-period 3 \
    --initial-position 0.0 0 0.0 0 \
    --forces-period-shift 0.5 \
    --sample-number 1000 \
    --optimization-function "hard_threshold_sparse_regression" \
    --algorithm "xlsindy" \
    --noise-level 0.0 \
    --no-implicit-regression

python single_test.py \
    --random-seed 12 14 \
    --experiment-folder "mujoco_align_data/cart_pole" \
    --max-time 20 \
    --forces-scale-vector 3.049855884605056 1.639574110558981 \
    --forces-period 3 \
    --initial-position 0.0 0 0.0 0 \
    --forces-period-shift 0.5 \
    --sample-number 1000 \
    --optimization-function "hard_threshold_sparse_regression" \
    --algorithm "xlsindy" \
    --noise-level 0.0 \
    --no-implicit-regression \
    --no-mujoco-generation


#some try after the classification add for the catalog 
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
    --no-mujoco-generation \
    --catalog-restriction 0 