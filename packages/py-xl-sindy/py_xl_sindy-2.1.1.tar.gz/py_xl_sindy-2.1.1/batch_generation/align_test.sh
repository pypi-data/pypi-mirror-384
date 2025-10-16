python -m batch_generation.v2.align_data \
        --experiment-file "results/56f0b72a1c2bddc8838e3d7359647a86" \
        --optimization-function "lasso_regression" \
        --algorithm "xlsindy" \
        --noise-level 0.3 \
        --random-seed 1 \
        --no-skip-already-done \
        --regression-type "mixed" \
        --print-graph

python -m batch_generation.v2.align_data \
        --experiment-file "results/56f0b72a1c2bddc8838e3d7359647a86" \
        --optimization-function "lasso_regression" \
        --algorithm "sindy" \
        --noise-level 0.0 \
        --random-seed 1 \
        --no-skip-already-done \
        --regression-type "mixed" \
        --print-graph