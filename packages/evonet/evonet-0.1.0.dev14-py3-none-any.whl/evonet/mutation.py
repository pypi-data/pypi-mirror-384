# SPDX-License-Identifier: MIT
"""
Mutation operations for evolvable neural networks.

Includes:
- Activation mutation
- Weight and bias mutation (Gaussian noise)
- Structural mutations: add/remove neurons and connections
"""

import random
from collections.abc import Collection
from typing import Literal, Optional, Union, cast

import numpy as np

from evonet.activation import ACTIVATIONS, random_function_name
from evonet.connection import Connection
from evonet.core import Nnet
from evonet.enums import ConnectionType, NeuronRole, RecurrentKind
from evonet.neuron import Neuron

ALL_ACTIVATIONS = "all"


def mutate_activation(neuron: Neuron, activations: list[str] | None = None) -> None:
    """
    Assign a new random activation function to a single neuron.

    Args:
        neuron (Neuron): The target neuron to mutate.
        activations (list[str] | None): Optional list of allowed activation names.
    """
    neuron.activation_name = random_function_name(activations)
    neuron.activation = ACTIVATIONS[neuron.activation_name]


def mutate_activations(
    net: Nnet,
    probability: float = 1.0,
    activations: Optional[list[str]] = None,
    layers: Optional[dict[int, Union[list[str], Literal["all"]]]] = None,
) -> None:
    """
    Mutate the activation functions of neurons with optional global or layer-specific
    control.

    Modes:
        A) Default: Hidden layers are mutated using all available activation functions.
        B) With `activations`: Hidden layers use a restricted set of activation
           functions.
        C) With `layers`: Only specified layers are mutated, each with their own
           activation sets. This mode overrides the `activations` argument.

    Args:
        net (Nnet): The target neural network.
        probability (float): Mutation probability per neuron (must be in [0, 1]).
        activations (list[str] | None): Optional list of allowed activation functions
                                        (used in mode B).
        layers (dict[int, list[str] | Literal["all"]] | None):
            Optional per-layer activation sets (mode C).
            If specified, overrides the `activations` argument.

    Notes:
        - Input and output layers are not mutated unless explicitly included
          in `layers`.
        - The function relies on `numpy.random.rand()` for random number generation.
        - The `mutate_activation` function is called to perform the actual mutation of
          a neuron's activation function.

    Raises:
        ValueError: If `probability` is not in [0, 1] or
                    if `layers` contains invalid layer indices.

    Example:
        >>> net = Nnet(...)  # Assume a neural network with 3 layers
        >>> mutate_activations(net, probability=0.5, activations=["relu", "sigmoid"])
        >>> mutate_activations(net, layers={1: ["relu"], 2: "all"}, probability=0.3)
    """

    if not 0 <= probability <= 1:
        raise ValueError("Probability must be between 0 and 1.")

    if layers is not None:
        max_layer = len(net.layers)
        invalid_layers = [i for i in layers if i < 0 or i >= max_layer]
        if invalid_layers:
            raise ValueError(
                f"Invalid layer indices: {invalid_layers}."
                f"Must be between 0 and {max_layer - 1}."
            )

    for layer_idx, layer in enumerate(net.layers):
        if layers is not None:
            if layer_idx not in layers:
                continue

            if layers[layer_idx] != ALL_ACTIVATIONS:
                layer_activations = cast(list[str], layers[layer_idx])
            else:
                layer_activations = None  # None: mutate_activation uses all activations

        elif layer_idx == 0 or layer_idx == len(net.layers) - 1:
            continue
        else:
            layer_activations = activations

        for neuron in layer.neurons:
            if np.random.rand() < probability:
                mutate_activation(neuron, layer_activations)


def mutate_weight(conn: Connection, std: float = 0.1) -> None:
    """Apply Gaussian noise to a connection weight."""
    conn.weight += np.random.normal(0, std)


def mutate_weights(net: Nnet, probability: float = 1.0, std: float = 0.1) -> None:
    """
    Apply Gaussian noise to weights of connections in the network.

    Args:
        net (Nnet): The target network.
        probability (float): Probability to mutate each connection.
        std (float): Standard deviation of the noise.
    """

    for conn in net.get_all_connections():
        if np.random.rand() < probability:
            mutate_weight(conn, std)


def mutate_bias(neuron: Neuron, std: float = 0.1) -> None:
    """Apply Gaussian noise to a neuron's bias value."""
    neuron.bias += np.random.normal(0, std)


def mutate_biases(net: Nnet, probability: float = 1.0, std: float = 0.1) -> None:
    """
    Apply Gaussian noise to biases of neurons in the network.

    Args:
        net (Nnet): The target network.
        probability (float): Mutation probability per neuron.
        std (float): Standard deviation of the noise.
    """
    for neuron in net.get_all_neurons():
        if neuron.role != NeuronRole.INPUT and np.random.rand() < probability:
            mutate_bias(neuron, std)


def add_random_connection(
    net: Nnet,
    allowed_recurrent: Optional[Collection[RecurrentKind | str]] = None,
    connection_init: Literal["zero", "random", "near_zero"] = "zero",
) -> bool:
    """
    Add a valid connection between two randomly chosen neurons.

    Rules:
    - Disallow connections into INPUT neurons.
    - Disallow duplicate (source, target) pairs.
    - Classify connection type by layer order:
        * src_layer < dst_layer  -> STANDARD
        * src_layer >= dst_layer -> RECURRENT
    - Recurrent edges are filtered by `allowed_recurrent`
      (list of 'direct' | 'lateral' | 'indirect').

    Args:
        net (Nnet): Target network to modify.
        allowed_recurrent (Collection[RecurrentKind | str] | None):
            Allowed recurrent connection kinds. Default: None (no recurrent edges).
        connection_init (Literal["zero", "random", "near_zero"]):
            Weight initialization mode for the new connection.
            - "zero":     Weight = 0.0 (neutral; ideal with HELI)
            - "random":   Weight ~ N(0, 0.5)
            - "near_zero": Weight ~ U(-0.05, 0.05)

    Returns:
        bool: True if a connection was added, False otherwise.
    """

    # Weight initialization
    if connection_init == "zero":
        weight = 0.0
    elif connection_init == "random":
        weight = np.random.randn() * 0.5
    elif connection_init == "near_zero":
        weight = np.random.uniform(-0.05, 0.05)
    else:
        raise ValueError(f"Unknown init mode: {connection_init}")

    # normalize to set[RecurrentKind]
    kinds: set[RecurrentKind] = set()
    if allowed_recurrent:
        for k in allowed_recurrent:
            kinds.add(RecurrentKind(k) if isinstance(k, str) else k)

    all_neurons = net.get_all_neurons()
    if len(all_neurons) < 2:
        return False

    # Build a dict of existing connections
    existing: set[tuple[Neuron, Neuron]] = {
        (c.source, c.target) for c in net.get_all_connections()
    }

    # neuron -> layer index
    layer_of: dict[Neuron, int] = {}
    for layer_idx, layer in enumerate(net.layers):
        for neuron in layer.neurons:
            layer_of[neuron] = layer_idx

    def classify(src: Neuron, dst: Neuron) -> tuple[bool, RecurrentKind | None]:
        src_layer_idx, dst_layer_idx = layer_of[src], layer_of[dst]
        if src is dst:
            return True, RecurrentKind.DIRECT
        if src_layer_idx == dst_layer_idx:
            return True, RecurrentKind.LATERAL
        if src_layer_idx > dst_layer_idx:
            return True, RecurrentKind.INDIRECT
        return False, None  # forward

    candidates: list[tuple[Neuron, Neuron]] = []
    for src in all_neurons:
        for dst in all_neurons:
            if dst.role == NeuronRole.INPUT:
                continue
            if (src, dst) in existing:
                continue

            is_recurrent, kind = classify(src, dst)
            if not is_recurrent:
                candidates.append((src, dst))  # forward always allowed
            elif kind in kinds:
                candidates.append((src, dst))  # recurrent allowed by policy

    if not candidates:
        return False

    src, dst = random.choice(candidates)
    src_layer_idx, dst_layer_idx = layer_of[src], layer_of[dst]
    conn_type = (
        ConnectionType.STANDARD
        if src_layer_idx < dst_layer_idx
        else ConnectionType.RECURRENT
    )

    net.add_connection(src, dst, weight=weight, conn_type=conn_type)
    return True


def remove_random_connection(net: Nnet) -> None:
    """
    Remove a randomly selected connection from the network.

    Does nothing if no connections are present.
    """
    all_connections = net.get_all_connections()
    if not all_connections:
        return

    conn = random.choice(all_connections)
    conn.source.outgoing.remove(conn)
    conn.target.incoming.remove(conn)


def add_random_neuron(
    net: Nnet,
    activations: list[str] | None = None,
    connection_init: Literal["zero", "random", "near_zero", "none"] = "zero",
) -> None:
    """
    Insert a new hidden neuron into a random layer.

    If the network has only input/output, a hidden layer is inserted.

    Args:
        net (Nnet): The target network.
        activations (list[str] | None): Optional list of allowed activation functions.
                                        If None, all registered activations are used.
    """
    if len(net.layers) < 2:
        return

    if len(net.layers) == 2:
        net.insert_layer(1)

    # Choose target layer (not input, not output)
    candidate_layers = net.layers[1:-1]
    if not candidate_layers:
        return

    layer = random.choice(candidate_layers)

    net.add_neuron(
        layer_idx=net.layers.index(layer),
        activation=random_function_name(activations),
        role=NeuronRole.HIDDEN,
        connection_init=connection_init,
    )


def remove_random_neuron(net: Nnet) -> None:
    """
    Remove a randomly selected hidden neuron from the network.

    All incoming and outgoing connections are also removed.
    """
    hidden_neurons = [n for n in net.get_all_neurons() if n.role == NeuronRole.HIDDEN]
    if not hidden_neurons:
        return

    neuron = random.choice(hidden_neurons)

    # Remove connections
    for conn in list(neuron.incoming):
        conn.source.outgoing.remove(conn)
    for conn in list(neuron.outgoing):
        conn.target.incoming.remove(conn)

    # Remove from layer
    for layer in net.layers:
        if neuron in layer.neurons:
            layer.neurons.remove(neuron)
            break


def split_connection(net: Nnet, activation: str = "tanh", noise: float = 0.1) -> None:
    """
    Insert a neuron in the middle of an existing connection.

    The old connection is removed, and two new ones are created:
    - from source → new neuron
    - from new neuron → target

    Args:
        net (Nnet): The target network.
        activation (str): Activation function for the new neuron.
        noise (float): Optional noise applied to new weights.
    """
    all_connections = net.get_all_connections()
    if not all_connections:
        return

    conn = random.choice(all_connections)
    src, dst = conn.source, conn.target

    insert_idx = None
    for idx, layer in enumerate(net.layers):
        if src in layer.neurons:
            insert_idx = idx + 1
            break

    if insert_idx is None or insert_idx >= len(net.layers):
        return

    new_neuron = net.add_neuron(
        layer_idx=insert_idx,
        role=NeuronRole.HIDDEN,
        activation=activation,
        connection_init="none",
    )[0]

    # Set new connections
    src.outgoing.remove(conn)
    dst.incoming.remove(conn)

    weight = 1.0 + np.random.normal(0, noise)
    net.add_connection(src, new_neuron, weight=weight)
    net.add_connection(new_neuron, dst, weight=conn.weight)
