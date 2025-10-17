# SPDX-License-Identifier: MIT
"""
Connection between neurons in an evolvable neural network.

A connection links a source neuron to a target neuron and transmits a weighted signal.
Supports optional connection types for specialized behaviors (e.g. inhibitory,
recurrent).
"""


from typing import TYPE_CHECKING

from evonet.enums import ConnectionType

if TYPE_CHECKING:
    from evonet.neuron import Neuron


class Connection:
    """
    Represents a directed, weighted connection between two neurons.

    Attributes:
        source (Neuron): The source neuron (presynaptic).
        target (Neuron): The target neuron (postsynaptic).
        weight (float): Multiplicative weight of the transmitted signal.
        delay (int): Optional delay in time steps (not yet implemented).
        type (ConnectionType): Type of connection (e.g. standard, recurrent,
                               inhibitory).
    """

    def __init__(
        self,
        source: "Neuron",
        target: "Neuron",
        weight: float = 1.0,
        delay: int = 0,
        conn_type: ConnectionType = ConnectionType.STANDARD,
    ) -> None:

        self.source = source
        self.target = target
        self.weight = weight
        self.delay = delay
        self.type: ConnectionType = conn_type

    def get_signal(self) -> float:
        """
        Return the weighted signal from the source neuron.

        Returns:
            float: source.output × weight
        """

        return self.source.output * self.weight

    def __repr__(self) -> str:
        """
        Return a concise string representation of the connection.

        Example:
            <Conn abc123 -> def456 w=0.85 type=standard>
        """

        type_str = self.type.name.lower()
        return (
            f"<Conn {self.source.id[:6]} "
            f"-> {self.target.id[:6]} "
            f"w={self.weight:.2f} type={type_str}>"
        )
