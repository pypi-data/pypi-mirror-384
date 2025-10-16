#generate

python batch_launch.py \
--experiment-folder "mujoco_align_data/cart_pole" \
--max-time 20 \
--number-coordinate 2 \
--forces-span 0.1 5 \
--number-experiment 10 \
--mode "generate" \
--random-seed 12 \
--sample-number 1000

python batch_launch.py \
--experiment-folder "mujoco_align_data/cart_pole_double" \
--max-time 20 \
--number-coordinate 3 \
--forces-span 0.1 5 \
--number-experiment 10 \
--mode "generate" \
--random-seed 13 \
--sample-number 3000

python batch_launch.py \
--experiment-folder "mujoco_align_data/double_pendulum_pm" \
--max-time 20 \
--number-coordinate 2 \
--forces-span 0.1 5 \
--number-experiment 10 \
--mode "generate" \
--random-seed 14 \
--sample-number 1000

# Create database and populate metrics

python create_validation_database.py

python batch_file_execute.py \
--script "exploration_metric" 

# Align on different Noise , regression algorithm , and paradigm

#XLSINDY

python batch_file_execute.py \
--script "align_data" \
--script_args "hard_threshold_sparse_regression" "xlsindy" 0.0 \
--random-seed 1

python batch_file_execute.py \
--script "align_data" \
--script_args "lasso_regression" "xlsindy" 0.0 \
--random-seed 1

python batch_file_execute.py \
--script "align_data" \
--script_args "hard_threshold_sparse_regression" "xlsindy" 0.05 \
--random-seed 1

python batch_file_execute.py \
--script "align_data" \
--script_args "lasso_regression" "xlsindy" 0.05 \
--random-seed 1

python batch_file_execute.py \
--script "align_data" \
--script_args "hard_threshold_sparse_regression" "xlsindy" 0.1 \
--random-seed 1

python batch_file_execute.py \
--script "align_data" \
--script_args "lasso_regression" "xlsindy" 0.1 \
--random-seed 1

python batch_file_execute.py \
--script "align_data" \
--script_args "hard_threshold_sparse_regression" "xlsindy" 0.001 \
--random-seed 1

python batch_file_execute.py \
--script "align_data" \
--script_args "lasso_regression" "xlsindy" 0.001 \
--random-seed 1

python batch_file_execute.py \
--script "align_data" \
--script_args "hard_threshold_sparse_regression" "xlsindy" 0.01 \
--random-seed 1

python batch_file_execute.py \
--script "align_data" \
--script_args "lasso_regression" "xlsindy" 0.01 \
--random-seed 1

#SINDY

python batch_file_execute.py \
--script "align_data" \
--script_args "hard_threshold_sparse_regression" "sindy" 0.0 \
--random-seed 1

python batch_file_execute.py \
--script "align_data" \
--script_args "lasso_regression" "sindy" 0.0 \
--random-seed 1

python batch_file_execute.py \
--script "align_data" \
--script_args "hard_threshold_sparse_regression" "sindy" 0.05 \
--random-seed 1

python batch_file_execute.py \
--script "align_data" \
--script_args "lasso_regression" "sindy" 0.05 \
--random-seed 1

python batch_file_execute.py \
--script "align_data" \
--script_args "hard_threshold_sparse_regression" "sindy" 0.1 \
--random-seed 1

python batch_file_execute.py \
--script "align_data" \
--script_args "lasso_regression" "sindy" 0.1 \
--random-seed 1

python batch_file_execute.py \
--script "align_data" \
--script_args "hard_threshold_sparse_regression" "sindy" 0.001 \
--random-seed 1

python batch_file_execute.py \
--script "align_data" \
--script_args "lasso_regression" "sindy" 0.001 \
--random-seed 1

python batch_file_execute.py \
--script "align_data" \
--script_args "hard_threshold_sparse_regression" "sindy" 0.01 \
--random-seed 1

python batch_file_execute.py \
--script "align_data" \
--script_args "lasso_regression" "sindy" 0.01 \
--random-seed 1

# Create database 

python create_panda_database.py