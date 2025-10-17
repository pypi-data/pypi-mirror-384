# tests/test_nnet_io_and_forward.py
import math

import numpy as np
import pytest

from evonet.core import Nnet
from evonet.enums import NeuronRole


def build_simple_ff_net() -> Nnet:
    """
    Build a small feed-forward network with topology 2 -> 3 -> 1, using 'linear'
    activations to keep expectations straightforward.

    Returns:
        Nnet: A network with input(2), hidden(3), output(1), fully connected
              between consecutive layers.
    """
    net = Nnet()
    # Create three layers: input, hidden, output
    net.add_layer()  # L0
    net.add_layer()  # L1
    net.add_layer()  # L2

    # Add neurons: inputs (no auto-connect from previous layer), then hidden & output
    net.add_neuron(
        layer_idx=0,
        role=NeuronRole.INPUT,
        activation="linear",
        count=2,
        connection_init="none",
    )
    net.add_neuron(
        layer_idx=1,
        role=NeuronRole.HIDDEN,
        activation="linear",
        count=3,
        connection_init="random",
    )
    net.add_neuron(
        layer_idx=2,
        role=NeuronRole.OUTPUT,
        activation="linear",
        count=1,
        connection_init="random",
    )
    return net


def test_weights_roundtrip_stable_order() -> None:
    """
    Ensure that get_weights() and set_weights() form a round-trip identity:

    set_weights(get_weights()) must leave the network weights unchanged, and setting a
    custom vector must be read back verbatim.
    """
    net = build_simple_ff_net()

    # Original read
    w0 = net.get_weights()
    assert (
        w0.ndim == 1 and w0.size > 0
    ), "Network should expose a non-empty flat weights vector."

    # Round-trip identity: set_weights(get_weights()) does not alter values
    net.set_weights(w0.copy())
    w1 = net.get_weights()
    assert np.allclose(
        w0, w1
    ), "Round-trip with identical vector should not change weights."

    # Write a deterministic pattern and read it back
    target = np.linspace(-1.0, 1.0, num=w0.size, dtype=float)
    net.set_weights(target)
    w2 = net.get_weights()
    assert np.allclose(
        w2, target
    ), "Weights written via set_weights() must be read back bitwise equal."


def test_biases_roundtrip_and_length_mismatch() -> None:
    """Verify that biases (excluding input neurons) round-trip correctly and that length
    mismatches are rejected with a clear ValueError."""
    net = build_simple_ff_net()

    b0 = net.get_biases()
    assert b0.ndim == 1, "Bias vector must be flat."
    # By convention, input biases are excluded (only hidden+output).
    assert b0.size == 3 + 1, "Expected biases for 3 hidden + 1 output neuron."

    # Round-trip with custom values
    target = np.arange(b0.size, dtype=float) * 0.1  # [0.0, 0.1, 0.2, 0.3]
    net.set_biases(target)
    b1 = net.get_biases()
    assert np.allclose(
        b1, target
    ), "Biases written via set_biases() must be read back verbatim."

    # Length mismatch must raise
    with pytest.raises(ValueError):
        net.set_biases(target[:-1])


def test_forward_sanity_linear_1x1() -> None:
    """
    Build a minimal 1->1 linear network and check a simple forward pass:

    y = w * x + b This ensures calc() respects weights and biases as set via the I/O
    helpers.
    """
    net = Nnet()
    net.add_layer()  # L0
    net.add_layer()  # L1
    net.add_neuron(
        layer_idx=0,
        role=NeuronRole.INPUT,
        activation="linear",
        count=1,
        connection_init="none",
    )
    net.add_neuron(
        layer_idx=1,
        role=NeuronRole.OUTPUT,
        activation="linear",
        count=1,
        connection_init="random",
    )

    # There should be exactly one connection L0(0) -> L1(0). Force known params:
    net.set_weights(np.array([2.0], dtype=float))  # w = 2.0
    net.set_biases(np.array([0.5], dtype=float))  # b = 0.5

    x = 3.0
    y = net.calc([x])  # calc resets states, applies inputs, and propagates outputs.
    assert isinstance(y, list) and len(y) == 1
    assert math.isclose(
        y[0], 2.0 * x + 0.5, rel_tol=1e-9
    ), "Forward output must equal w*x + b for linear activation."
