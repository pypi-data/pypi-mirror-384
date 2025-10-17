# SPDX-License-Identifier: MIT
"""
Activation functions for evolvable neural networks.

Includes standard nonlinearities (ReLU, Tanh, Sigmoid), linear and threshold functions,
modern smooth activations (Swish, Mish), and a softmax utility.

All functions are scalar-based and stateless, unless noted otherwise.
"""

import random
from typing import Callable, List, Tuple, Union

import numpy as np

Scalar = Union[int, float]


# Common Activation Functions


def tanh(x: Scalar) -> float:
    """Hyperbolic tangent activation: [-inf, inf] --> [-1, 1]."""
    return float(np.tanh(x))


def ntanh(x: Scalar) -> float:
    """Normalized tanh: (tanh(x) + 1) / 2 --> [0, 1]."""
    return (np.tanh(x) + 1) / 2


def sigmoid(x: Scalar) -> float:
    """Sigmoid/logistic function: [-inf, inf] --> [0, 1]."""
    x = np.clip(float(x), -500, 500)
    return 1 / (1 + np.exp(-x))


def relu(x: Scalar) -> float:
    """ReLU: max(0, x)."""
    return max(0.0, float(x))


def relu_max1(x: Scalar) -> float:
    """ReLU clipped to [0, 1]."""
    return min(max(0.0, float(x)), 1.0)


def leaky_relu(x: Scalar, alpha: float = 0.01) -> float:
    """Leaky ReLU: x if x ≥ 0 else alpha * x."""
    x = float(x)
    return x if x >= 0 else alpha * x


def elu(x: Scalar, alpha: float = 1.0) -> float:
    """Exponential Linear Unit."""
    x = float(x)
    return x if x >= 0 else alpha * (np.exp(x) - 1)


def selu(x: Scalar, alpha: float = 1.67326324, scale: float = 1.05070098) -> float:
    """Scaled Exponential Linear Unit (SELU)."""
    x = float(x)
    return scale * x if x >= 0 else scale * alpha * (np.exp(x) - 1)


def gaussian(x: Scalar) -> float:
    """Gaussian bell function: exp(-x^2)."""
    x = float(x)
    if np.abs(x) > 38:
        return 0.0
    return np.exp(-(x**2))


# Threshold Functions


def binary(x: Scalar) -> float:
    """Step function: 1 if x > 0 else 0."""
    return 1.0 if x > 0 else 0.0


def signum(x: Scalar) -> float:
    """Sign function: 1, -1 or 0 depending on sign of x."""
    return 1.0 if x > 0 else -1.0 if x < 0 else 0.0


# Linear Variants


def linear(x: Scalar) -> float:
    """Linear identity: returns x."""
    return float(x)


def linear_max1(x: Scalar) -> float:
    """Linear function clipped to [-1, 1]."""
    return min(max(-1.0, float(x)), 1.0)


def invert(x: Scalar) -> float:
    """Returns -x."""
    return -float(x)


def null(_: Scalar = 0) -> float:
    """Always returns 0.0."""
    return 0.0


# Modern Functions


def swish(x: Scalar) -> float:
    """Swish activation: x * sigmoid(x). Smooth and non-monotonic."""
    return float(x) * sigmoid(x)


def mish(x: Scalar) -> float:
    """Mish activation: x * tanh(softplus(x))."""
    return float(x) * np.tanh(np.log1p(np.exp(x)))


def softplus(x: Scalar) -> float:
    """Smooth ReLU approximation: log(1 + exp(x))."""
    return np.log1p(np.exp(float(x)))


def softsign(x: Scalar) -> float:
    """Smooth alternative to tanh: x / (1 + |x|)."""
    return float(x) / (1 + abs(float(x)))


def hard_sigmoid(x: Scalar) -> float:
    """Piecewise linear approximation of sigmoid."""
    return min(max(0.0, 0.2 * float(x) + 0.5), 1.0)


# Special Functions


def softmax(values: Union[List[float], Tuple[float], np.ndarray]) -> np.ndarray:
    """
    Applies softmax over a list of values.

    Args:
        values: Array-like input with ≥2 values.

    Returns:
        np.ndarray: Normalized softmax output summing to 1.
    """
    arr = np.array(values, dtype=float)
    if arr.size < 2:
        raise ValueError("Softmax input must have at least two values")
    exp_x = np.exp(arr - np.max(arr))  # For numerical stability
    return exp_x / np.sum(exp_x)


def random_function_name(activations: list[str] | None = None) -> str:
    """
    Return a random activation function name from the registry.

    Args:
        activations (list[str] | None): Optional subset of allowed function names.
            If None, all registered activation names are considered.

    Raises:
        ValueError: If any name is not in the activation registry.

    Returns:
        str: Randomly selected activation function name.
    """

    if activations is None:
        activations = list(ACTIVATIONS.keys())

    invalid = set(activations) - set(ACTIVATIONS.keys())
    if invalid:
        raise ValueError(f"Invalid activation functions: {invalid}")

    return random.choice(activations)


# Registry

ACTIVATIONS: dict[str, Callable] = {
    "tanh": tanh,
    "ntanh": ntanh,
    "sigmoid": sigmoid,
    "relu": relu,
    "relu_max1": relu_max1,
    "leaky_relu": leaky_relu,
    "elu": elu,
    "selu": selu,
    "gaussian": gaussian,
    "binary": binary,
    "signum": signum,
    "linear": linear,
    "linear_max1": linear_max1,
    "invert": invert,
    "null": null,
    "swish": swish,
    "mish": mish,
    "softplus": softplus,
    "softsign": softsign,
    "hard_sigmoid": hard_sigmoid,
    "softmax": softmax,
}
