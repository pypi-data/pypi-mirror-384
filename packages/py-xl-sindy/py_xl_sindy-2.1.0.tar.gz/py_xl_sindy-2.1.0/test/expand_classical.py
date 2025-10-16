import xlsindy

import numpy as np

ard = np.array([2, 5, 4])

expand = np.array([[1, 0], [0, 1], [1, 0]])

print(xlsindy.symbolic_util.classical_sindy_expand_catalog(ard, expand))
