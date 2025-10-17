# SPDX-License-Identifier: MIT
"""
Neuron class for evolvable neural networks.

Each neuron holds an activation function, input/output connections, a bias term, and
stores intermediate values (input, output, last_output) during computation.
"""

from typing import Callable
from uuid import uuid4

from evonet.activation import ACTIVATIONS
from evonet.connection import Connection
from evonet.enums import NeuronRole


class Neuron:
    """
    Represents a single neuron within the network.

    A neuron receives inputs via incoming connections, applies an activation
    function to the sum of its inputs and bias, and transmits the result
    to its outgoing connections.

    Attributes:
        id (str): Unique identifier (UUID, shortened for readability).
        role (NeuronRole): Role of the neuron (INPUT, HIDDEN, OUTPUT, BIAS).
        activation_name (str): Name of the activation function used.
        activation (Callable): The actual activation function (e.g. tanh, relu).
        bias (float): Additive scalar bias (only used if role != INPUT).
        incoming (list[Connection]): Incoming connections from other neurons.
        outgoing (list[Connection]): Outgoing connections to target neurons.
        input (float): Accumulated input before activation.
        output (float): Activation output (after applying function).
        last_output (float): Output from the previous timestep (used for recurrent
                             links).
        label (str): Optional human-readable label (used in visualizations).
    """

    def __init__(
        self, activation: str = "tanh", label: str = "", bias: float = 0.0
    ) -> None:

        if activation not in ACTIVATIONS:
            raise ValueError(f"Unknown activation function: '{activation}'")
        self.id: str = str(uuid4())
        self.role: NeuronRole = NeuronRole.HIDDEN
        self.activation_name: str = activation
        self.activation: Callable[[float], float] = ACTIVATIONS[activation]
        self.bias: float = bias
        self.incoming: list[Connection] = []
        self.outgoing: list[Connection] = []
        self.input: float = 0.0
        self.output: float = 0.0
        self.last_output: float = 0.0
        self.label = label

    def reset(self, full: bool = False) -> None:
        """
        Clear current neuron state for a new forward pass.

        Args:
            full (bool): If True, also clears `last_output` (used for recurrent memory).

        This method:
        - Always resets `input` and `output`.
        - Only resets `last_output` if `full=True`.

        Use `full=True` if the neuron should forget its prior state
        (e.g. after fitness evaluation).
        """

        self.output = 0.0
        self.input = 0.0
        if full:
            self.last_output = 0.0

    def __repr__(self) -> str:
        """
        Return a concise string representation of the neuron.

        Example:
            Neuron id=ab12cd act=tanh role=HIDDEN bias=0.00 input=0.12345 output=0.67890
        """

        return (
            f"Neuron id={self.id[:6]} "
            f"act={self.activation_name} "
            f"role={self.role} "
            f"bias={self.bias:.2f} "
            f"input={self.input:0.5f} "
            f"output={self.output:0.5f}"
        )

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Neuron) and self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)
