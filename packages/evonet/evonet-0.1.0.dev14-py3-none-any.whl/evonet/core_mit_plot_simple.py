# SPDX-License-Identifier: MIT
"""
Core class for evolvable neural networks.

Manages neurons, layers, and connections with explicit topology. Supports forward passes
with optional recurrent connections across time steps, mutation/crossover hooks, and
export interfaces.
"""

from __future__ import annotations

from typing import Literal, Optional

import graphviz
import numpy as np
import matplotlib.pyplot as plt

from evonet.activation import softmax as softmax_vec
from evonet.connection import Connection
from evonet.enums import ConnectionType, NeuronRole, RecurrentKind
from evonet.layer import Layer
from evonet.neuron import Neuron


class Nnet:
    """
    Evolvable neural network with explicit layered topology.

    Attributes:
        layers (list[Layer]): Ordered list of network layers.
    """

    def __init__(self) -> None:
        self.layers: list[Layer] = []

    @property
    def num_weights(self) -> int:
        """Number of connections in the network (no allocation)."""
        return len(self.get_all_connections())

    @property
    def num_biases(self) -> int:
        """
        Return the number of trainable biases (excludes input neurons).

        Inputs are feature holders and have no trainable bias in this design.
        """
        count = 0
        for layer in self.layers:
            for neuron in layer.neurons:
                if neuron.role is not NeuronRole.INPUT:
                    count += 1
        return count

    @property
    def num_params(self) -> int:
        """Total parameter count = weights + biases."""
        return self.num_weights + self.num_biases

    def add_layer(self, count: int = 1) -> int:
        """
        Append one or more empty layers to the network.

        Args:
            count (int): Number of layers to add (must be > 0).

        Returns:
            int: Index of the last added layer.

        Raises:
            ValueError: If count is not positive.
        """

        if count <= 0:
            raise ValueError("Number of layers must be greater then zero")

        for _ in range(count):
            self.layers.append(Layer())

        return len(self.layers) - 1

    def insert_layer(self, index: int) -> None:
        """
        Insert an empty layer at a given index.

        Args:
            index (int): Position to insert the new layer (0 = before input).

        Raises:
            ValueError: If index is out of bounds.
        """

        if not (0 <= index <= len(self.layers)):
            raise ValueError(f"insert_layer: index {index} out of bounds.")
        self.layers.insert(index, Layer())

    def add_neuron(
        self,
        layer_idx: int | None = None,
        activation: str = "tanh",
        bias: float = 0.0,
        label: str = "",
        role: NeuronRole = NeuronRole.HIDDEN,
        count: int = 1,
        connection_init: Literal["random", "zero", "none"] = "random",
        recurrent: Optional[set[RecurrentKind]] = None,
    ) -> list[Neuron]:
        """
        Add one or more neurons to the network.

        Args:
            layer_idx: Target layer index. Defaults to last layer.
            activation: Activation function name.
            bias: Initial bias value.
            label: Optional label.
            role: Role of the neuron (INPUT, HIDDEN, OUTPUT).
            count: Number of neurons to add (default: 1).
            connection_init:
                "random" – connect with random weights (feedforward + recurrent)
                "zero"   – connect with weight 0.0 (feedforward + recurrent)
                "none"   – do not create connections (feedforward + recurrent)
            recurrent: Optional recurrent connection types.

        Returns:
            list[Neuron]: List of added neurons.
        """
        if layer_idx is None:
            layer_idx = len(self.layers) - 1  # Add neuron to last layer

        if layer_idx < 0:
            raise ValueError(f"Layer index must be >= 0 (got {layer_idx})")
        if layer_idx >= len(self.layers):
            raise ValueError(f"Layer index out of bounds: {layer_idx}")

        target_layer = self.layers[layer_idx]
        new_neurons: list[Neuron] = []

        # Create neurons without connections
        for _ in range(count):
            neuron = Neuron(activation=activation, bias=bias)
            neuron.role = role
            neuron.label = label
            target_layer.neurons.append(neuron)
            new_neurons.append(neuron)

        # Weights based on init mode
        weight_map = {"random": None, "zero": 0.0, "none": None}
        if connection_init not in weight_map:
            raise ValueError(f"Invalid connection_init: {connection_init}")
        weight = weight_map[connection_init]

        skip_connections = connection_init == "none"

        # Connect to previous layer
        if not skip_connections and layer_idx > 0:
            for prev_neuron in self.layers[layer_idx - 1].neurons:
                for n in new_neurons:
                    self.add_connection(prev_neuron, n, weight=weight)

        # Connect to next layer (hidden only)
        if (
            not skip_connections
            and role == NeuronRole.HIDDEN
            and layer_idx < len(self.layers) - 1
        ):
            for next_neuron in self.layers[layer_idx + 1].neurons:
                for n in new_neurons:
                    self.add_connection(n, next_neuron, weight=weight)

        # Recurrent connections
        if recurrent and not skip_connections:
            if RecurrentKind.DIRECT in recurrent:
                for n in new_neurons:
                    if n.role == NeuronRole.HIDDEN:
                        self.add_connection(
                            n, n, weight=weight, conn_type=ConnectionType.RECURRENT
                        )

            if RecurrentKind.LATERAL in recurrent:
                full_layer = list(self.layers[layer_idx].neurons)
                for src in full_layer:
                    for dst in new_neurons:
                        if src is not dst:
                            self.add_connection(
                                src,
                                dst,
                                weight=weight,
                                conn_type=ConnectionType.RECURRENT,
                            )

            if RecurrentKind.INDIRECT in recurrent:
                for src in new_neurons:
                    for lower_layer in self.layers[1:layer_idx]:
                        for dst in lower_layer.neurons:
                            self.add_connection(
                                src,
                                dst,
                                weight=weight,
                                conn_type=ConnectionType.RECURRENT,
                            )
                for higher_layer in self.layers[layer_idx + 1 :]:
                    for src in higher_layer.neurons:
                        for dst in new_neurons:
                            self.add_connection(
                                src,
                                dst,
                                weight=weight,
                                conn_type=ConnectionType.RECURRENT,
                            )

        return new_neurons

    def add_connection(
        self,
        source: Neuron,
        target: Neuron,
        weight: float | None = None,
        conn_type: ConnectionType = ConnectionType.STANDARD,
    ) -> None:
        """
        Create a directed connection between two neurons.

        Args:
            source (Neuron): Source neuron.
            target (Neuron): Target neuron.
            weight (float | None): Initial weight. If None, random value is used.
            conn_type (ConnectionType): Type of connection (e.g. standard, recurrent).
        """

        if weight is None:
            weight = np.random.randn() * 0.5

        conn = Connection(source, target, weight=weight, conn_type=conn_type)
        source.outgoing.append(conn)
        target.incoming.append(conn)

    def reset(self, full: bool = False) -> None:
        """Reset all neurons (clears input, output, and caches)."""
        for layer in self.layers:
            for neuron in layer.neurons:
                neuron.reset(full=full)

    def calc(self, input_values: list[float]) -> list[float]:
        """
        Perform a forward pass through the network.

        Args:
            input_values (list[float]): Input vector (must match input layer size).

        Returns:
            list[float]: Output values from the last layer.

        Raises:
            AssertionError: If input size does not match input layer.
        """

        # Save LAST OUTPUT
        for layer in self.layers:
            for neuron in layer.neurons:
                neuron.last_output = neuron.output

        self.reset()

        # Set inputs
        input_layer = self.layers[0]
        assert len(input_layer.neurons) == len(input_values)
        for i, n in enumerate(input_layer.neurons):
            n.input = float(input_values[i])

        # Preload recurrent contributions from previous time step (last_output)
        for layer in self.layers:
            for n in layer.neurons:
                for c in n.incoming:
                    if c.type is ConnectionType.RECURRENT:
                        c.target.input += c.weight * c.source.last_output

        # Feed-forward by layers: activate first, then propagate non-recurrent edges
        for layer in self.layers:

            # Apply softmax to all neurons with activation_name == "softmax"
            softmax_neurons = [
                n for n in layer.neurons if n.activation_name == "softmax"
            ]
            if softmax_neurons:
                if len(softmax_neurons) >= 2:
                    # Normal softmax behaviour
                    totals = [n.input + n.bias for n in softmax_neurons]
                    probabilities = softmax_vec(totals)
                    for n, p in zip(softmax_neurons, probabilities):
                        n.output = float(p)
                else:
                    # Fallback: single softmax neuron acts like identity
                    n = softmax_neurons[0]
                    n.output = n.input + n.bias

            # Activate all neurons in this layer
            for n in layer.neurons:
                if n.activation_name != "softmax":
                    total = n.input + n.bias
                    n.output = n.activation(total)

            # Propagate to targets (exclude recurrent edges)
            for n in layer.neurons:
                for c in n.outgoing:
                    if c.type is not ConnectionType.RECURRENT:
                        c.target.input += c.weight * n.output

        return [n.output for n in self.layers[-1].neurons]

    def get_all_neurons(self) -> list[Neuron]:
        """Return all neurons in all layers (flattened)."""
        return [n for layer in self.layers for n in layer.neurons]

    def get_all_connections(self) -> list[Connection]:
        """Return all outgoing connections in the network."""
        return [c for n in self.get_all_neurons() for c in n.outgoing]

    def __repr__(self) -> str:
        total_neurons = sum(len(layer.neurons) for layer in self.layers)
        input_neurons = len(self.layers[0].neurons) if self.layers else 0
        output_neurons = len(self.layers[-1].neurons) if len(self.layers) > 1 else 0
        hidden_neurons = total_neurons - input_neurons - output_neurons

        total_connections = len(self.get_all_connections())

        return (
            f"<Nnet | {len(self.layers)} layers, "
            f"{total_neurons} neurons (I:{input_neurons} H:{hidden_neurons} "
            f"O:{output_neurons}), "
            f"{total_connections} connections "
        )

    def print_graph(
        self,
        name: str,
        engine: str = "dot",
        labels_on: bool = True,
        colors_on: bool = True,
        thickness_on: bool = False,
        fillcolors_on: bool = False,
    ) -> None:
        """
        Render a visual representation of the network using Graphviz.

        Args:
            name (str): Output file name (without extension).
            engine (str): Graphviz layout engine (e.g., 'dot', 'neato').
            labels_on (bool): Whether to show edge weights as labels.
            colors_on (bool): Whether to color edges by sign.
            thickness_on (bool): Whether to scale edge thickness by weight.
            fillcolors_on (bool): Whether to color neurons by role.
        """

        if not self.layers:
            print("No layers to visualize.")
            return

        dot = graphviz.Digraph(name=name, format="png", engine=engine)
        dot.graph_attr.update(
            bgcolor="white",
            rankdir="LR",
            overlap="prism",
            sep="15",
            ratio="fill",
            splines="spline",
            size="6.68,5!",
            dpi="600",
        )
        dot.node_attr.update(
            shape="circle", style="filled", fixedsize="shape", width="1.8"
        )
        dot.edge_attr.update(arrowsize="0.8")

        # Add neurons with coordinates (x = layer, y = index)
        for layer_idx, layer in enumerate(self.layers):
            for neuron_idx, neuron in enumerate(layer.neurons):
                if neuron.role.name == "INPUT":
                    fillcolor = "lightblue" if fillcolors_on else "white"
                elif neuron.role.name == "OUTPUT":
                    fillcolor = "orange" if fillcolors_on else "white"
                else:
                    fillcolor = "lightgreen" if fillcolors_on else "white"

                label = (
                    f"{neuron.label or neuron.role.name}({layer_idx})\n"
                    f"In: {neuron.input:.3f}\n"
                    f"Out: {neuron.output:.3f}\n"
                    f"LastOut: {neuron.last_output:.3f}\n"
                    f"Bias: {neuron.bias:.3f}\n"
                    f"{neuron.activation_name}"
                )

                pos = f"{layer_idx},{-neuron_idx}!"
                dot.node(
                    name=neuron.id,
                    label=label,
                    fillcolor=fillcolor,
                    pos=pos,
                )

        # Add edges
        for conn in self.get_all_connections():
            label = f"{conn.weight:.2f}" if labels_on else ""
            color = (
                "green"
                if colors_on and conn.weight >= 0
                else "red" if colors_on else "black"
            )
            penwidth = (
                str(max(1, min(5, abs(conn.weight * 5)))) if thickness_on else "1"
            )
            style = "dashed" if conn.type.name == "RECURRENT" else "solid"

            dot.edge(
                conn.source.id,
                conn.target.id,
                label=label,
                color=color,
                penwidth=penwidth,
                style=style,
            )

        dot.render(name, cleanup=True)

    def plot_simple(
        net,
        show_weights: bool = False,
        show_values: bool = True,
        path: str | None = None,
    ) -> None:
        """
        Visualize the network in a simple layered layout using Matplotlib.

        Args:
            net: The Nnet object to visualize.
            show_weights (bool): If True, draw weight values on edges.
            show_values (bool): If True, neuron output values are shown,
                                else neuron indices.
            path (str | None): If given, save the plot to this path instead
                               of displaying.
        """

        fig, ax = plt.subplots(figsize=(8, 6))
        ax.set_aspect("equal")
        ax.axis("off")

        neuron_positions: dict = {}

        # Place neurons
        for layer_idx, layer in enumerate(net.layers):
            y_positions = list(range(len(layer.neurons)))
            offset = (
                max(len(layer.neurons) for layer in net.layers) - len(y_positions)
            ) / 2.0

            for neuron_idx, neuron in enumerate(layer.neurons):
                x, y = layer_idx, neuron_idx + offset
                neuron_positions[neuron] = (x, y)

                ax.scatter(
                    x,
                    y,
                    c="royalblue",
                    s=400,
                    zorder=3,
                    edgecolors="white",
                    linewidths=1.5,
                )

                label = f"{neuron.output:.2f}" if show_values else str(neuron_idx)
                ax.text(
                    x,
                    y,
                    label,
                    ha="center",
                    va="center",
                    color="white",
                    fontsize=9,
                    zorder=4,
                )

        # Draw connections
        for layer in net.layers[1:]:
            for neuron in layer.neurons:
                x2, y2 = neuron_positions[neuron]
                for conn in neuron.incoming:
                    x1, y1 = neuron_positions[conn.source]
                    style = "--" if getattr(conn, "recurrent", False) else "-"
                    color = "crimson" if getattr(conn, "recurrent", False) else "gray"
                    ax.plot(
                        [x1, x2],
                        [y1, y2],
                        color=color,
                        linestyle=style,
                        alpha=0.7,
                        zorder=1,
                    )

                    if show_weights:
                        xm, ym = (x1 + x2) / 2, (y1 + y2) / 2
                        ax.text(
                            xm,
                            ym,
                            f"{conn.weight:.2f}",
                            fontsize=7,
                            color="black",
                            alpha=0.6,
                        )

        plt.tight_layout()

        if path:
            plt.savefig(path, dpi=150)
            plt.close(fig)
        else:
            plt.show()

    def _build_index_map(self) -> dict[Neuron, tuple[int, int]]:
        """Build a mapping from neuron -> (layer_idx, neuron_idx) for O(1) lookups."""
        index_map: dict[Neuron, tuple[int, int]] = {}
        for layer_idx, layer in enumerate(self.layers):
            for neuron_idx, neuron in enumerate(layer.neurons):
                index_map[neuron] = (layer_idx, neuron_idx)
        return index_map

    def get_weights(self) -> np.ndarray:
        """
        Return all connection weights as a flat vector in a deterministic order.

        Returns:
            np.ndarray: 1D array of connection weights.

        Order key:
            (src_layer_idx, src_neuron_idx, dst_layer_idx,
            dst_neuron_idx, connection_type)
        """
        conns = self.get_all_connections()
        if not conns:
            return np.empty(0, dtype=float)

        index_map = self._build_index_map()

        def sort_key(c: Connection) -> tuple[int, int, int, int, int]:
            src_layer_idx, src_neuron_idx = index_map[c.source]
            dst_layer_idx, dst_neuron_idx = index_map[c.target]
            return (
                src_layer_idx,
                src_neuron_idx,
                dst_layer_idx,
                dst_neuron_idx,
                int(c.type.value),
            )

        conns_sorted = sorted(conns, key=sort_key)
        return np.array([c.weight for c in conns_sorted], dtype=float)

    def set_weights(self, flat: np.ndarray) -> None:
        """
        Set all connection weights from a flat vector using the same deterministic order
        as `get_weights()`.

        Args:
            flat (np.ndarray): Flat array of weights (must match number of connections).

        Raises:
            ValueError: If the length of the array does not match.
        """
        flat = np.asarray(flat, dtype=float).ravel()

        conns = self.get_all_connections()
        if not conns and flat.size == 0:
            return

        index_map = self._build_index_map()

        def sort_key(c: Connection) -> tuple[int, int, int, int, int]:
            src_layer_idx, src_neuron_idx = index_map[c.source]
            dst_layer_idx, dst_neuron_idx = index_map[c.target]
            return (
                src_layer_idx,
                src_neuron_idx,
                dst_layer_idx,
                dst_neuron_idx,
                int(c.type.value),
            )

        conns_sorted = sorted(conns, key=sort_key)

        if flat.size != len(conns_sorted):
            raise ValueError(
                f"Length mismatch for weights: expected {len(conns_sorted)}, "
                f"got {flat.size}."
            )

        for weight_value, conn in zip(flat, conns_sorted):
            conn.weight = float(weight_value)

    def get_biases(self) -> np.ndarray:
        """
        Return all trainable biases as a flat vector (excluding input neurons).

        Returns:
            np.ndarray: Bias vector.

        Order:
            (layer_index, neuron_index) over all non-input neurons.
        """

        if not self.layers:
            return np.empty(0, dtype=float)

        biases: list[float] = []
        for _, layer in enumerate(self.layers):
            for _, neuron in enumerate(layer.neurons):
                if neuron.role is not NeuronRole.INPUT:
                    biases.append(neuron.bias)
        return np.asarray(biases, dtype=float)

    def set_biases(self, flat: np.ndarray) -> None:
        """
        Set all neuron biases (excluding input neurons) from a flat vector using the
        same ordering as `get_biases()`.

        Args:
            flat (np.ndarray): Bias values in deterministic order.

        Raises:
            ValueError: If length does not match the number of biases.
        """
        flat = np.asarray(flat, dtype=float).ravel()

        # Collect non-input neurons in deterministic order
        targets: list[Neuron] = []
        for _, layer in enumerate(self.layers):
            for _, neuron in enumerate(layer.neurons):
                if neuron.role is not NeuronRole.INPUT:
                    targets.append(neuron)

        if flat.size != len(targets):
            raise ValueError(
                f"Length mismatch for biases: expected {len(targets)}, got {flat.size}."
            )

        for b, n in zip(flat, targets):
            n.bias = float(b)
