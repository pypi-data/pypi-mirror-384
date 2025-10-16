
# python batch_launch.py \
# --experiment-folder "mujoco_align_data/cart_pole" \
# --max-time 20 \
# --number-coordinate 2 \
# --forces-span 0.1 8 \
# --number-experiment 3 \
# --mode "generate" \
# --random-seed 12 \
# --sample-number 1000

# python batch_launch.py \
# --experiment-folder "mujoco_align_data/cart_pole_double" \
# --max-time 20 \
# --number-coordinate 3 \
# --forces-span 0.1 8 \
# --number-experiment 3 \
# --mode "generate" \
# --random-seed 13 \
# --sample-number 3000

# python batch_launch.py \
# --experiment-folder "mujoco_align_data/double_pendulum_pm" \
# --max-time 20 \
# --number-coordinate 2 \
# --forces-span 0.1 8 \
# --number-experiment 3 \
# --mode "generate" \
# --random-seed 14 \
# --sample-number 1000

# python create_validation_database.py

# python batch_file_execute.py \
# --script "exploration_metric" 

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
--script_args "hard_threshold_sparse_regression" "xlsindy" 0.1 \
--random-seed 1

python batch_file_execute.py \
--script "align_data" \
--script_args "lasso_regression" "xlsindy" 0.1 \
--random-seed 1

python batch_file_execute.py \
--script "align_data" \
--script_args "hard_threshold_sparse_regression" "xlsindy" 1 \
--random-seed 1

python batch_file_execute.py \
--script "align_data" \
--script_args "lasso_regression" "xlsindy" 1 \
--random-seed 1

python batch_file_execute.py \
--script "align_data" \
--script_args "hard_threshold_sparse_regression" "xlsindy" 0.01 \
--random-seed 1

python batch_file_execute.py \
--script "align_data" \
--script_args "lasso_regression" "xlsindy" 0.01 \
--random-seed 1

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
--script_args "hard_threshold_sparse_regression" "sindy" 0.1 \
--random-seed 1

python batch_file_execute.py \
--script "align_data" \
--script_args "lasso_regression" "sindy" 0.1 \
--random-seed 1

python batch_file_execute.py \
--script "align_data" \
--script_args "hard_threshold_sparse_regression" "sindy" 1 \
--random-seed 1

python batch_file_execute.py \
--script "align_data" \
--script_args "lasso_regression" "sindy" 1 \
--random-seed 1

python batch_file_execute.py \
--script "align_data" \
--script_args "hard_threshold_sparse_regression" "sindy" 0.01 \
--random-seed 1

python batch_file_execute.py \
--script "align_data" \
--script_args "lasso_regression" "sindy" 0.01 \
--random-seed 1

python batch_file_execute.py \
--script "validation_trajectory" \
--script_args 20 \
--random-seed 1

python create_panda_database.py


## Visualisation purpose

python mujoco_generate_data.py \
--experiment-folder "mujoco_align_data/cart_pole_double" \
--max-time 20 \
--forces-scale-vector 3.294015408619446 0.014118377794475162 4.885851855619996 \
--forces-period 3.0 \
--forces-period-shift 0.5 \
--random-seed 13 2 \
--mujoco-viewer

python mujoco_generate_data.py \
--experiment-folder "mujoco_align_data/double_pendulum_pm" \
--max-time 20 \
--forces-scale-vector 3.4417371468964832 2.9428825539647843 \
--forces-period 3.0 \
--forces-period-shift 0.5 \
--random-seed 14 2 \
--mujoco-record

python validation_trajectory.py \
--experiment-file "result.keep/double_pendulum_pm__142_20250221_134019_keep" \
--max-time 20 \
--plot \
--random-seed 2 \
--record

