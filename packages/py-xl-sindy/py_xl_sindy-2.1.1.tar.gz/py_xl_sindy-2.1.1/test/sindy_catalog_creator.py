import numpy as np
import sympy as sp

import xlsindy


def create_coefficient_matrices(lists):
    """
    Given a list of lists, where each inner list contains tuples of (coefficient, expression),
    returns:
      - unique_exprs: a sorted list of unique sympy expressions.
      - coeff_matrix: a 2D numpy array (dtype=object) of shape (number of unique expressions, n)
                      with the coefficient for the corresponding expression in each list.
      - binary_matrix: a 2D numpy integer array with 1 if the corresponding coefficient is non-zero, 0 otherwise.
    """
    # Collect all expressions from all lists.
    all_exprs = [expr for sublist in lists for (_, expr) in sublist]

    # Create a list of unique expressions. Sorting (here by string representation) ensures a reproducible order.
    unique_exprs = np.array(sorted(list(set(all_exprs)), key=lambda expr: str(expr)))

    num_exprs = len(unique_exprs)
    num_lists = len(lists)

    # Create a mapping from expression to its row index.
    expr_to_index = {expr: i for i, expr in enumerate(unique_exprs)}

    # Initialize coefficient matrix with zeros.
    coeff_matrix = np.zeros((num_exprs, num_lists), dtype=object)

    # Fill in the coefficient matrix.
    for col, sublist in enumerate(lists):
        for coeff, expr in sublist:
            row = expr_to_index[expr]
            coeff_matrix[row, col] = coeff

    # It's possible that some entries remain as the default 0 (which is fine)
    # Now create a binary matrix: 1 if coefficient is nonzero, 0 otherwise.
    binary_matrix = np.zeros((num_exprs, num_lists), dtype=int)
    for i in range(num_exprs):
        for j in range(num_lists):
            # Use != 0; works with sympy numbers as well.
            if coeff_matrix[i, j] != 0:
                binary_matrix[i, j] = 1

    return unique_exprs, coeff_matrix, binary_matrix


def translate_coeff_matrix(
    coeff_matrix: np.ndarray, expand_matrix: np.ndarray
) -> np.ndarray:
    """
    Translate the coefficient matrix into a column vector corresponding to the ordering
    of the expanded catalog matrix (as produced by classical_sindy_expand_catalog).

    Args:
        coeff_matrix (np.ndarray): A matrix of shape (len(catalog), n) containing the coefficients.
        expand_matrix (np.ndarray): A binary matrix of shape (len(catalog), n) that indicates
                                    where each catalog function is applied (1 means applied).

    Returns:
        np.ndarray: A column vector of shape (expand_matrix.sum(), 1) containing the coefficients,
                    in the order that matches the expanded catalog.
    """
    # Flatten the expand matrix in row-major order and find indices where its value is 1.
    indices = np.where(expand_matrix.ravel() == 1)[0]
    # Compute the elementwise product and extract the coefficients corresponding to the ones.
    coeff_flat = (coeff_matrix * expand_matrix).ravel()[indices]
    # Reshape into a column vector.
    coeff_vector = coeff_flat.reshape(-1, 1)
    return coeff_vector


# Example usage:
x, y, z = sp.symbols("x y z")
list1 = [(3, x), (5, y), (-2, z), (7, 1)]
list2 = [(2, x), (0, y), (4, z)]
list3 = [(1, x), (3, 1), (6, z)]  # an example additional list

lists = [list1, list2, list3]
unique_exprs, coeff_matrix, binary_matrix = create_coefficient_matrices(lists)

print("Unique expressions:")
print(unique_exprs)
print("\nCoefficient matrix:")
print(coeff_matrix)
print("\nBinary matrix:")
print(binary_matrix)

expand = xlsindy.symbolic_util.classical_sindy_expand_catalog(unique_exprs, binary_matrix)

solution = translate_coeff_matrix(coeff_matrix, binary_matrix)

print("everyone shape :", expand.shape, solution.shape)

print("retrieved :", expand.T @ solution)
