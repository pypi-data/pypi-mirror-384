# SPDX-License-Identifier: MIT
"""
Lightweight layer container for neurons in an evolvable neural network.

A Layer groups neurons at the same depth (e.g., input, hidden, output) and is used to
organize the network topology explicitly.
"""

from evonet.neuron import Neuron


class Layer:
    """
    Represents a single layer in the network.

    A layer is simply a list of neurons. No computation or connectivity logic is handled
    here — only structural grouping.
    """

    def __init__(self) -> None:
        """Initialize an empty neuron list."""
        self.neurons: list[Neuron] = []

    def add_neuron(self, neuron: Neuron) -> None:
        """Add a neuron to this layer."""
        self.neurons.append(neuron)
