# SPDX-License-Identifier: MIT
"""
Enumerations used in evolvable neural networks.

Includes:
- Neuron roles (input, hidden, output, bias)
- Connection types (standard, recurrent, modulatory, etc.)
"""

from enum import Enum, auto


class NeuronRole(Enum):
    """
    Role of a neuron in the network.

    - INPUT: Receives external input (no bias, no activation)
    - HIDDEN: Internal processing neuron
    - OUTPUT: Final layer neuron providing network output
    - BIAS: Internal-only constant additive bias.
    """

    INPUT = auto()
    HIDDEN = auto()
    OUTPUT = auto()
    BIAS = auto()


class ConnectionType(Enum):
    """
    Type of connection between neurons.

    - STANDARD: Regular forward connection
    - INHIBITORY: Reduces or suppresses target activation
    - EXCITATORY: Amplifies target activation
    - MODULATORY: Alters other connections or gates
    - RECURRENT: Connects to earlier time step (feedback)
    """

    STANDARD = auto()
    INHIBITORY = auto()
    EXCITATORY = auto()
    MODULATORY = auto()
    RECURRENT = auto()


class RecurrentKind(str, Enum):
    DIRECT = "direct"  # src == dst
    LATERAL = "lateral"  # same layer, src != dst
    INDIRECT = "indirect"  # src_layer > dst_layer (back edge)


# Neutral activation functions
# These functions satisfy f(0) ≈ 0 and are safe for zero-weight initialization.
NEUTRAL_ACTIVATIONS: list[str] = [
    "tanh",
    "relu",
    "relu_max1",
    "leaky_relu",
    "elu",
    "selu",
    "linear",
    "linear_max1",
    "invert",
    "swish",
    "mish",
    "softsign",
]
