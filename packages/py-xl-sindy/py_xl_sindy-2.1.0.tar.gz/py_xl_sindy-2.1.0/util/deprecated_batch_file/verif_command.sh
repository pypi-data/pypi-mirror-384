
# verif of validation trajectory

python display_data.py \
--experiment-file "result/cart_pole__120_20250221_133956" \
--optimization-function ""hard_threshold_sparse_regression"" \
--algorithm "sindy" \
--noise-level 0 \
--random-seed 12

python validation_trajectory.py \
--experiment-file "result/cart_pole__122_20250221_134001" \
--max-time 20 \
--random-seed 2

python validation_trajectory_v2.py \
--experiment-file "result/cart_pole__120_20250221_133956" \
--max-time 20 \
--random-seed 2

python align_data.py \
--experiment-file "result/cart_pole__122_20250221_134001" \
--optimization-function ""hard_threshold_sparse_regression"" \
--algorithm "sindy" \
--noise-level 0.0 \
--random-seed 13 \
--no-skip-already-done \
--no-validation-on-database

python align_data.py \
--experiment-file "result/cart_pole_double__132_20250221_134011" \
--optimization-function ""lasso_regression"" \
--algorithm "sindy" \
--noise-level 0.0 \
--random-seed 1 \
--no-skip-already-done \
--no-validation-on-database

python validation_trajectory.py \
--experiment-file "result/cart_pole_double__132_20250221_134011" \
--max-time 20 \
--random-seed 2

python validation_trajectory.py \
--experiment-file "result/cart_pole__120_20250221_135658" \
--max-time 20 \
--random-seed 2


cart_pole__120_20250221_135658