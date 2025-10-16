# Test again in the mixed case

# Full Implicit regression

python single_test.py \
    --random-seed 12 15 \
    --experiment-folder "mujoco_align_data/cart_pole" \
    --max-time 10 \
    --forces-scale-vector 0 0 \
    --initial-position 0.0 0 0.0 0 \
    --forces-period 3 \
    --forces-period-shift 0.5 \
    --sample-number 200 \
    --optimization-function "hard_threshold_sparse_regression" \
    --algorithm "sindy" \
    --noise-level 0.0 \
    --regression-type "mixed" \
    --no-mujoco-generation \
    --batch-number 10 \
    --initial-condition-randomness 1 4 4 4 \
    --catalog-restriction 12 \
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
    --sample-number 200 \
    --optimization-function "hard_threshold_sparse_regression" \
    --algorithm "xlsindy" \
    --noise-level 0.0 \
    --regression-type "mixed" \
    --no-mujoco-generation \
    --batch-number 10 \
    --initial-condition-randomness 1 \
    --catalog-restriction -1 \
    --no-implicit-regression-debug \
    --implicit-regression-lamba 1e-7

# Full Explicit regress

python single_test.py \
    --random-seed 12 15 \
    --experiment-folder "mujoco_align_data/cart_pole" \
    --max-time 20 \
    --forces-scale-vector 3 3 \
    --initial-position 0.0 0 0.0 0 \
    --forces-period 3 \
    --forces-period-shift 0.5 \
    --sample-number 200 \
    --optimization-function "hard_threshold_sparse_regression" \
    --algorithm "xlsindy" \
    --noise-level 0.0 \
    --regression-type "mixed" \
    --no-mujoco-generation \
    --batch-number 1 \
    --initial-condition-randomness 0 \
    --catalog-restriction -1 \
    --no-implicit-regression-debug \
    --implicit-regression-lamba 1e-7

python single_test.py \
    --random-seed 12 15 \
    --experiment-folder "mujoco_align_data/cart_pole" \
    --max-time 20 \
    --forces-scale-vector 3 3 \
    --initial-position 0.0 0 0.0 0 \
    --forces-period 3 \
    --forces-period-shift 0.5 \
    --sample-number 200 \
    --optimization-function "hard_threshold_sparse_regression" \
    --algorithm "sindy" \
    --noise-level 0.0 \
    --regression-type "mixed" \
    --no-mujoco-generation \
    --batch-number 1 \
    --initial-condition-randomness 0 \
    --catalog-restriction -1 \
    --no-implicit-regression-debug \
    --implicit-regression-lamba 1e-7

# Mixed regression 

python single_test.py \
    --random-seed 12 15 \
    --experiment-folder "mujoco_align_data/cart_pole" \
    --max-time 10 \
    --forces-scale-vector 0 3 \
    --initial-position 0.0 0 0.0 0 \
    --forces-period 1 \
    --forces-period-shift 0.2 \
    --sample-number 200 \
    --optimization-function "lasso_regression" \
    --algorithm "sindy" \
    --noise-level 0.0 \
    --regression-type "mixed" \
    --no-mujoco-generation \
    --batch-number 6 \
    --initial-condition-randomness 1 \
    --catalog-restriction -1 \
    --no-implicit-regression-debug \
    --implicit-regression-lamba 1e-7

python single_test.py \
    --random-seed 12 15 \
    --experiment-folder "mujoco_align_data/cart_pole" \
    --max-time 5 \
    --forces-scale-vector 0 5 \
    --initial-position 0.0 0 0.0 0 \
    --forces-period 3 \
    --forces-period-shift 0.5 \
    --sample-number 2000 \
    --optimization-function "hard_threshold_sparse_regression" \
    --algorithm "sindy" \
    --noise-level 0.0 \
    --regression-type "mixed" \
    --no-mujoco-generation \
    --batch-number 20 \
    --initial-condition-randomness 3 \
    --catalog-restriction -1 \
    --no-implicit-regression-debug \
    --implicit-regression-lamba 1e-7