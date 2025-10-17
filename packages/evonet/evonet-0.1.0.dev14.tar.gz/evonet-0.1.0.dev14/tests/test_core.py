from evonet.core import Nnet
from evonet.enums import NeuronRole


def test_forward_pass_identity() -> None:
    """Tests a minimal feedforward network with identity mapping."""
    net = Nnet()
    net.add_layer()  # Input layer
    net.add_layer()  # Output layer

    net.add_neuron(
        layer_idx=0,
        activation="linear",
        role=NeuronRole.INPUT,
        label="in",
        connection_init="none",
    )
    net.add_neuron(
        layer_idx=1,
        activation="linear",
        role=NeuronRole.OUTPUT,
        label="out",
        connection_init="none",
    )

    src = net.layers[0].neurons[0]
    dst = net.layers[1].neurons[0]

    net.add_connection(src, dst, weight=1.0)

    # Gewicht prüfen
    assert abs(src.outgoing[0].weight - 1.0) < 1e-6

    result = net.calc([0.75])

    assert isinstance(result, list)
    assert len(result) == 1
    assert abs(result[0] - 0.75) < 1e-6


def test_forward_pass_with_bias() -> None:
    """Tests a simple net with bias on the output neuron."""
    net = Nnet()
    net.add_layer()
    net.add_layer()

    net.add_neuron(
        layer_idx=0,
        activation="linear",
        role=NeuronRole.INPUT,
        label="in",
        connection_init="none",
    )
    net.add_neuron(
        layer_idx=1,
        activation="linear",
        role=NeuronRole.OUTPUT,
        bias=0.5,
        label="out",
        connection_init="none",
    )

    src = net.layers[0].neurons[0]
    dst = net.layers[1].neurons[0]

    net.add_connection(src, dst, weight=2.0)

    # Gewicht prüfen
    assert abs(src.outgoing[0].weight - 2.0) < 1e-6

    result = net.calc([1.0])

    assert isinstance(result, list)
    assert len(result) == 1
    assert abs(result[0] - 2.5) < 1e-6  # (1.0 * 2.0) + 0.5 = 2.5
