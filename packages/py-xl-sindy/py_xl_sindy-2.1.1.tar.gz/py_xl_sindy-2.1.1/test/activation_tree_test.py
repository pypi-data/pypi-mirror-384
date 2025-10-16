from xlsindy.optimization import activated_catalog
import numpy as np

def fake_exp_matrix(catalog_prop, sampled_steps):
    """
    Create a fake experiment matrix for testing purposes.

    Args:
        catalog_prop (np.ndarray(num_coords, catalog_lenght)): propagation catalog.
        sampled_steps (int): Number of sampled steps.

    Returns:
        np.ndarray: Fake experiment matrix.
    """
    # Repeat each row of catalog_prop 'sampled_steps' times
    return np.repeat(catalog_prop, sampled_steps, axis=0)

def fake_force(presence,sampled_steps):
    """
    Create a fake force array for testing purposes.

    Args:
        presence (np.ndarray(num_coordinate,1)): Whether the force is present or not.
        sampled_steps (int): Number of sampled steps.

    Returns:
        np.ndarray: Fake force array.
    """
    # Create a fake force array with the same shape as the catalog_prop
    return np.repeat(presence, sampled_steps, axis=1)


def test_1_propagation():
    """
    Test the propagation of the activation.
    """

    sampled_step = 10

    catalog_prop = np.array([[0, 0, 1], [0, 1, 0],[0,0,0]]).T

    presense = np.array([[1, 0, 1]]).T

    force = fake_force(presense, sampled_step)
    exp_matrix = fake_exp_matrix(catalog_prop, sampled_step)

    # Activation propagation
    activated_function,activated_catalogs = activated_catalog(
        exp_matrix,
        force
    )

    assert not bool(np.any(activated_catalogs != np.array([[1, 0, 1]]).T ))

    assert not bool(np.any(activated_function != np.array([[1, 0, 0]]) ))

def test_2_propagation():
    """
    Test the propagation of the activation.
    """

    sampled_step = 10

    catalog_prop = np.array([[0, 0, 1], [0, 1, 0],[0,0,0]]).T

    presense = np.array([[0, 0, 0]]).T

    force = fake_force(presense, sampled_step)
    exp_matrix = fake_exp_matrix(catalog_prop, sampled_step)

    # Activation propagation
    activated_function,activated_catalogs = activated_catalog(
        exp_matrix,
        force
    )

    assert not bool(np.any(activated_catalogs != np.array([[0, 0, 0]]).T ))

    assert not bool(np.any(activated_function != np.array([[0, 0, 0]]) ))

def test_3_propagation():
    """
    Test the propagation of the activation.
    """

    sampled_step = 10

    catalog_prop = np.array([[1, 0, 1], [0, 1, 0],[0,0,0]]).T

    presense = np.array([[0, 0, 1]]).T

    force = fake_force(presense, sampled_step)
    exp_matrix = fake_exp_matrix(catalog_prop, sampled_step)

    # Activation propagation
    activated_function,activated_catalogs = activated_catalog(
        exp_matrix,
        force
    )

    assert not bool(np.any(activated_catalogs != np.array([[1, 0, 1]]).T ))

    assert not bool(np.any(activated_function != np.array([[1, 0, 0]]) ))


def test_4_propagation():
    """
    Test the propagation of the activation.
    """

    sampled_step = 10

    catalog_prop = np.array([[1, 0, 1], [0, 1, 1],[0,0,0]]).T

    presense = np.array([[1, 0, 0]]).T

    force = fake_force(presense, sampled_step)
    exp_matrix = fake_exp_matrix(catalog_prop, sampled_step)

    # Activation propagation
    activated_function,activated_catalogs = activated_catalog(
        exp_matrix,
        force
    )

    assert not bool(np.any(activated_catalogs != np.array([[1, 1, 1]]).T ))

    assert not bool(np.any(activated_function != np.array([[1, 1, 0]]) ))

