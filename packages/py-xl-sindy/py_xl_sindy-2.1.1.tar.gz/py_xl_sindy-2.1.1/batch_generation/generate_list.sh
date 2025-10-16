#!/usr/bin/env bash

# Launch this script from the root of the repository.

python -m batch_generation.v2.generate_data \
    --random-seed 1 \
    --damping-coefficients -0.8 -1.3 \
    --batch-number 10 \
    --generation-type "mujoco" \
    --experiment-folder "util/mujoco_align_data/cart_pole" \
    --max-time 10 \
    --forces-scale-vector 0 5 \
    --initial-condition-randomness 3 \
    --initial-position 0.0 0 0.0 0 \
    --forces-period 3 \
    --forces-period-shift 0.5 \
    --sample-number 2000 \