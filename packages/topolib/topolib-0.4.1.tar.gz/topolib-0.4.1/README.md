# Topolib 🚀


[![Python Version](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-lightgrey.svg)](LICENSE)
[![Issues](https://img.shields.io/badge/issues-on%20GitLab-blue.svg)](https://gitlab.com/DaniloBorquez/topolib/-/issues)
[![Develop coverage](https://gitlab.com/DaniloBorquez/topolib/badges/develop/coverage.svg)](https://gitlab.com/DaniloBorquez/topolib/-/pipelines?ref=develop)
[![Release coverage](https://gitlab.com/DaniloBorquez/topolib/badges/release/coverage.svg)](https://gitlab.com/DaniloBorquez/topolib/-/pipelines?ref=release)
[![Documentation Status](https://readthedocs.org/projects/topolib/badge/?version=latest)](https://topolib.readthedocs.io/en/latest/?badge=latest)

A compact Python library for working with optical network topologies: nodes, links, metrics and visualization tools. 🌐

## Overview

Topolib models network topologies with three main modules:

- `topolib.elements` — Definitions of elementary building blocks
  - `Node` — represents a network node with id, name and geographic coordinates
  - `Link` — connects two `Node` objects and stores link length and id

- `topolib.topology` — High-level topology model
  - `Topology` — holds nodes and links, provides methods to add/remove nodes and links, compute metrics, export JSON, and compute shortest/disjoint paths
  - `Path` — represents a path through the topology

- `topolib.analysis` — Metrics and analysis helpers
  - `Metrics` — functions to compute node degree, link length statistics, connection matrices, etc.

- `topolib.visualization` — Visualization helpers
  - `MapView` — functions to display topology with OSM or paper-style maps

(These components are derived from the project's class diagram in `diagrams/class_diagram.puml`.)

## Features
- Modular design: elements, topology, analysis, and visualization
- Easy-to-use classes for nodes, links, and paths
- Built-in metrics and analysis helpers
- JSON import/export and interoperability
- Ready for Sphinx, Read the Docs, and PyPI

## Quickstart ⚡

Create and activate a virtual environment, install dev dependencies and run tests:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
python -m pip install -r dev-requirements.txt
python -m pytest -q
```

## Installation

```bash
pip install topolib
```

Or for development:

```bash
git clone https://gitlab.com/DaniloBorquez/topolib.git
cd topolib
python -m venv .venv
source .venv/bin/activate
pip install -e .
pip install -r dev-requirements.txt
```

## Documentation

Full documentation: [https://topolib.readthedocs.io/](https://topolib.readthedocs.io/)

## Basic usage example

```py
from topolib.elements.node import Node
from topolib.topology.topology import Topology

# Create nodes
n1 = Node(1, 'A', 10.0, 20.0)
n2 = Node(2, 'B', 11.0, 21.0)

# Build topology
topo = Topology()
topo.add_node(n1)
topo.add_node(n2)
# add links, compute metrics, visualize
```


## Development 🛠️

See `CONTRIBUTING.md` for development guidelines, commit message rules and pre-commit setup.



## Class diagram

![](diagrams/class_diagram.puml)

(If you prefer a rendered image of the UML, render the PlantUML file locally or in your CI pipeline.)

## License

See `LICENSE` in the project root.
