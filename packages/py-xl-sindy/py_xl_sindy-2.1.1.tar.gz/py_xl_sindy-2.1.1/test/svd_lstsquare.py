"""
SVD Least Squares Example with Feature Amputation

This tiny test clearly demonstrate that it is not possible to amputate simply the SVD matrix , because it doesn't modify the behavior of the least square solution...
I will need to clearly benchmark implicit sindy because it is not clear.
"""

import numpy as np



def generate_data(num_points=100, num_features=3, noise_std=0.1):
    np.random.seed(53)  # For reproducibility
    X = np.random.randn(num_points, num_features)
    true_coeffs = np.random.randn(num_features)
    true_coeffs[2]= 0
    y = X @ true_coeffs + np.random.randn(num_points) * noise_std
    return X, y, true_coeffs

def svd_least_squares(X, y):
    # Perform SVD decomposition
    U, S, VT = np.linalg.svd(X, full_matrices=False)
    S_inv = np.diag(1/S)
    # Compute the pseudoinverse
    X_pinv = VT.T @ S_inv @ U.T
    # Solve for coefficients
    coeffs = X_pinv @ y
    return coeffs, U, S, VT

def svd_least_squares_modified(U, S, VT, y, feature_to_remove):
    # Remove the specified feature from the pseudoinverse
    S_inv = np.diag(1/S)
    X_pinv_modified = VT.T @ S_inv @ U.T
    X_pinv_modified = np.delete(X_pinv_modified, feature_to_remove, axis=0)
    # Solve for coefficients with the modified pseudoinverse
    coeffs = X_pinv_modified @ y
    return coeffs

def svd_least_squares_modified_2(U, S, VT, y, feature_to_remove):
    # Zero out the specified feature in U
    U_modified = U.copy()
    U_modified[:, feature_to_remove] = 0

    # Recompute pseudoinverse using modified U
    S_inv = np.diag(1/S)
    X_pinv_modified = VT.T @ S_inv @ U_modified.T
    coeffs = X_pinv_modified @ y
    return coeffs

def svd_least_squares_modified_3(U, S, VT, y, feature_to_remove):
    # Zero out the specified feature in U
    U_modified = U.copy()

    D= np.diag(np.ones(U_modified.shape[0]))
    D[feature_to_remove, feature_to_remove] = 0

    # Recompute pseudoinverse using modified U
    S_inv = np.diag(1/S)
    X_pinv_modified = VT.T @ S_inv @ U_modified.T @ D
    coeffs = X_pinv_modified @ y
    return coeffs

def main():
    # Generate synthetic data
    X, y, true_coeffs = generate_data(num_points=200, num_features=5, noise_std=0.05)
    
    # Solve using SVD
    fitted_coeffs, U, S, VT = svd_least_squares(X, y)

    print("True Coefficients:", true_coeffs)
    print("Fitted Coefficients:", fitted_coeffs)
    print("Error (L2 norm):", np.linalg.norm(true_coeffs - fitted_coeffs))

    # Remove a feature
    feature_to_remove = 2
    X_amputed = np.delete(X, feature_to_remove, axis=1)

    # Solve using SVD on amputed X
    fitted_coeffs_amputed, _, _, _ = svd_least_squares(X_amputed, y)

    # Solve using modified pseudoinverse
    fitted_coeffs_modified = svd_least_squares_modified(U, S, VT, y, feature_to_remove)

    fitted_coeffs_modified_2 = svd_least_squares_modified_2(U, S, VT, y, feature_to_remove)

    fitted_coeffs_modified_3 = svd_least_squares_modified_3(U, S, VT, y, feature_to_remove)

    print("\nFitted Coefficients after Amputing Feature {} (SVD on X_amputed):".format(feature_to_remove), fitted_coeffs_amputed)
    print("Fitted Coefficients after Amputing Feature {} (Modified X_pinv):".format(feature_to_remove), fitted_coeffs_modified)
    print("Fitted Coefficients after Zeroing U Feature {} (Modified U):".format(feature_to_remove), fitted_coeffs_modified_2)
    print("Fitted Coefficients after Zeroing U Feature {} (Added discarding):".format(feature_to_remove), fitted_coeffs_modified_3)
    print("Error between amputed and modified coefficients (L2 norm):", np.linalg.norm(fitted_coeffs_amputed - fitted_coeffs_modified))

if __name__ == "__main__":
    main()
