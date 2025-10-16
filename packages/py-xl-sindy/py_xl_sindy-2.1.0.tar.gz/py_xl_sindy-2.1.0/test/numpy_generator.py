import numpy as np

rng1 = np.random.default_rng(["11", "31", 2])

rng2 = np.random.default_rng([12, 31, 2])

print(rng1.random(), rng2.random())
