import xlsindy.symbolic_util
import numpy as np

catalog = np.arange(5) + 12

expand_matrix = np.ones((5, 2), int)

expand_matrix[1, 0] = 0

expand_matrix[3, 1] = 0

print(xlsindy.symbolic_util.classical_sindy_expand_catalog(catalog, expand_matrix))
