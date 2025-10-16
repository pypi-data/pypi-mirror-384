python mujoco_generate_data.py \
--experiment-folder "mujoco_align_data/cart_pole_double" \
--max-time 20 \
--forces-scale-vector 1 1 1 \
--forces-period 3 \
--forces-period-shift 0.5 \
--random-seed 12 \
--sample-number 1000 

python align_data.py \
--experiment-file "cart_pole_double__20250214_164920" \
--optimization-function "lasso_regression" \
--algorithm "xlsindy"

python align_data.py \
--experiment-file "cart_pole_double__20250214_172043" \
--optimization-function ""hard_threshold_sparse_regression"" \
--algorithm "xlsindy"

#After the rework
python align_data.py \
--experiment-file "result/cart_pole__121_20250217_175541" \
--optimization-function ""hard_threshold_sparse_regression"" \
--algorithm "xlsindy" \
--noise-level 0.0 \
--random-seed 12

python align_data.py \
--experiment-file "result/cart_pole_double__130_20250217_175855" \
--optimization-function ""hard_threshold_sparse_regression"" \
--algorithm "xlsindy" \
--noise-level 0.0 \
--random-seed 12

python align_data.py \
--experiment-file "result/double_pendulum_pm__140_20250217_180211" \
--optimization-function ""hard_threshold_sparse_regression"" \
--algorithm "xlsindy" \
--noise-level 0.0 \
--random-seed 12

#Everything work fine !!

#  change in the verification

#SINDY VERIFICATION

python align_data.py \
--experiment-file "result/cart_pole__120_20250220_170619" \
--optimization-function ""hard_threshold_sparse_regression"" \
--algorithm "xlsindy" \
--noise-level 0.0 \
--random-seed 12

python align_data.py \
--experiment-file "result/cart_pole__120_20250220_170619" \
--optimization-function ""hard_threshold_sparse_regression"" \
--algorithm "sindy" \
--noise-level 0.0 \
--random-seed 12

python align_data.py \
--experiment-file "result/cart_pole_double__130_20250220_170625" \
--optimization-function ""hard_threshold_sparse_regression"" \
--algorithm "xlsindy" \
--noise-level 0.0 \
--random-seed 12

python align_data.py \
--experiment-file "result/cart_pole_double__130_20250220_170625" \
--optimization-function ""hard_threshold_sparse_regression"" \
--algorithm "sindy" \
--noise-level 0.0 \
--random-seed 12

python align_data.py \
--experiment-file "result/double_pendulum_pm__140_20250220_170629" \
--optimization-function ""hard_threshold_sparse_regression"" \
--algorithm "xlsindy" \
--noise-level 0.0 \
--random-seed 12

python align_data.py \
--experiment-file "result/double_pendulum_pm__140_20250220_170629" \
--optimization-function ""hard_threshold_sparse_regression"" \
--algorithm "sindy" \
--noise-level 0.0 \
--random-seed 12

## OMG IT WORKS 

#SINDY random catalog

python align_data.py \
--experiment-file "result/cart_pole__120_20250221_124728" \
--optimization-function ""hard_threshold_sparse_regression"" \
--algorithm "sindy" \
--noise-level 0.0 \
--random-seed 12
