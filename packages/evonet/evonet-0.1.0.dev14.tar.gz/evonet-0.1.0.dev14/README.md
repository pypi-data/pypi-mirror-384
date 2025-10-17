# EvoNet
[![Code Quality & Tests](https://github.com/EvoLib/evo-net/actions/workflows/ci.yml/badge.svg)](https://github.com/EvoLib/evo-net/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Project Status: Alpha](https://img.shields.io/badge/status-alpha-orange.svg)](https://github.com/EvoLib/evo-net)

**EvoNet** is a modular and evolvable neural network core designed for integration with [EvoLib](https://github.com/EvoLib/evo-lib).
It supports dynamic topologies, recurrent connections, per-neuron activation, and structural evolution – with a strong emphasis on **clarity**, **transparency**, and **didactic value**.

---

## Features

- **Layer-based but flexible** – allows skip connections, cycles, and recurrent paths
- **Typed neuron roles and connection types** (`NeuronRole`, `ConnectionType`)
- **Topology-aware mutation system** – add/remove neurons and connections, mutate weights, change activations
- **Per-neuron activation functions** – configurable, extensible, evolvable
- **1-step recurrent state logic** – avoids multi-pass stabilization
- **Topology can grow at runtime** – with `add_neuron`, `add_connection`, `split_connection`
- **Debug-friendly architecture** – explicit IDs, labels, roles, directional graphs
- **Designed for evolutionary learning** – mutation, crossover, speciation ready
- **Lightweight & extensible** – pure Python, NumPy-based, no hard dependencies

---

> ⚠️ **This project is in early development (alpha)**. Interfaces and structure may change.

---

## Quick Example

```python
from evonet.core import Nnet

net = Nnet()
net.add_layer()  # Input
net.add_layer()  # Output

net.add_neuron(layer_idx=0, activation="linear", lable="in")
net.add_neuron(layer_idx=1, activation="linear", bias=0.5, lable="out", connect_layer=True)

print(net.calc([1.0]))
```

## License

MIT License - see [MIT License](https://github.com/EvoLib/evo-net/tree/main/LICENSE).

