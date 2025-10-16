python mujoco_generate_data.py \
--experiment-folder "mujoco_align_data/cart_pole_double" \
--max-time 20 \
--forces-scale-vector 7 4.5 3.2 \
--forces-period 3 \
--forces-period-shift 0.5 \
--random-seed 13 13 \
--sample-number 3000 

python align_data.py \
--experiment-file "result/cart_pole_double__1313_20250221_135729" \
--optimization-function "lasso_regression" \
--algorithm "xlsindy" \
--no-skip-already-done

python align_data.py \
--experiment-file "result/cart_pole_double__1313_20250221_135729" \
--optimization-function ""hard_threshold_sparse_regression"" \
--algorithm "xlsindy" \
--no-skip-already-done

python align_data.py \
--experiment-file "result/cart_pole_double__1313_20250424_125517" \
--optimization-function "lasso_regression" \
--algorithm "sindy"

python align_data.py \
--experiment-file "result/cart_pole_double__1313_20250424_125517" \
--optimization-function ""hard_threshold_sparse_regression"" \
--algorithm "sindy"