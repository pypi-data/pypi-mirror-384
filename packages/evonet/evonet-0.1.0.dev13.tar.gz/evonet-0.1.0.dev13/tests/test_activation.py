import numpy as np
import pytest

from evonet import activation


@pytest.mark.parametrize("x", [-2.0, 0.0, 2.0])
def test_activation_outputs_finite(x: float) -> None:
    """All scalar activations should return a finite float."""
    for name, fn in activation.ACTIVATIONS.items():
        if name == "softmax":
            continue  # handled separately
        y = fn(x)
        assert isinstance(y, float), f"{name} did not return float"
        assert np.isfinite(y), f"{name} returned non-finite value: {y}"


def test_softmax_sum_to_one() -> None:
    """Softmax output should sum to 1.0."""
    input_vector = [1.0, 2.0, 3.0]
    output = activation.softmax(input_vector)
    assert isinstance(output, np.ndarray)
    np.testing.assert_almost_equal(np.sum(output), 1.0, decimal=6)


def test_random_function_name_exists_in_registry() -> None:
    """random_function_name must return a valid name in the registry."""
    for _ in range(10):
        name = activation.random_function_name()
        assert name in activation.ACTIVATIONS
