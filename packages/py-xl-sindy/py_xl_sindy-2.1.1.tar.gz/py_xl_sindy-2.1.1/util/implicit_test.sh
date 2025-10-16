python mujoco_generate_data.py \
--experiment-folder "mujoco_align_data/double_pendulum_pm" \
--max-time 20 \
--forces-scale-vector 0 0 \
--forces-period 3 \
--forces-period-shift 0.5 \
--random-seed 12 \
--sample-number 1000 \
--mujoco-record

python align_data.py \
--experiment-file "result/double_pendulum_pm__12_20250423_111100" \
--optimization-function "lasso_regression" \
--algorithm "xlsindy" \
--implicit-regression \
--no-skip-already-done