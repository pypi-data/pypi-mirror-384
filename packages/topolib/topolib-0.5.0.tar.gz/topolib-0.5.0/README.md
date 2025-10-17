# Topolib 🚀
# Topolib 🚀

[![Python Version](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-lightgrey.svg)](LICENSE)
[![Issues](https://img.shields.io/badge/issues-on%20GitLab-blue.svg)](https://gitlab.com/DaniloBorquez/topolib/-/issues)
[![Develop coverage](https://gitlab.com/DaniloBorquez/topolib/badges/develop/coverage.svg)](https://gitlab.com/DaniloBorquez/topolib/-/pipelines?ref=develop)
[![Release coverage](https://gitlab.com/DaniloBorquez/topolib/badges/release/coverage.svg)](https://gitlab.com/DaniloBorquez/topolib/-/pipelines?ref=release)
[![Documentation Status](https://readthedocs.org/projects/topolib/badge/?version=latest)](https://topolib.readthedocs.io/en/latest/?badge=latest)

> **Topolib** is a compact, modular Python library for modeling, analyzing, and visualizing optical network topologies.  
> **Goal:** Provide researchers and engineers with a simple, extensible toolkit for working with nodes, links, metrics, and map-based visualizations.  
>   
> 🌐 **Model** | 📊 **Analyze** | 🗺️ **Visualize** | 🧩 **Extend**

---

## 📂 Examples

Explore ready-to-run usage examples in the [`examples/`](examples/) folder!  
- [Show topology on a map](examples/show_topology_in_map.py) 🗺️  
- [Export topology to CSV and JSON](examples/export_csv_json.py) 📄
- [Export topology and k-shortest paths for FlexNetSim](examples/export_flexnetsim.py) 🔀

---

## 🧭 Overview

Topolib is organized into four main modules:

- 🧱 **Elements:** `Node`, `Link` — basic building blocks
- 🕸️ **Topology:** `Topology`, `Path` — manage nodes, links, paths, and adjacency
- 📈 **Analysis:** `Metrics` — compute node degree, link stats, connection matrices
- 🖼️ **Visualization:** `MapView` — plot topologies on real maps

---

## ✨ Features

- Modular, extensible design
- Easy-to-use classes for nodes, links, and paths
- Built-in metrics and analysis helpers
- JSON import/export and interoperability
- Ready for Sphinx, Read the Docs, and PyPI

---

## ⚡ Quickstart

```bash
python -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install topolib
```

---

## 📚 Documentation

Full documentation: [https://topolib.readthedocs.io/](https://topolib.readthedocs.io/)

---

## 📝 Basic usage

```python
from topolib.elements.node import Node
from topolib.topology.topology import Topology

n1 = Node(1, 'A', 10.0, 20.0)
n2 = Node(2, 'B', 11.0, 21.0)
topo = Topology(nodes=[n1, n2])
# Add links, compute metrics, visualize, etc.
```

---

## 🛠️ Development

See [`CONTRIBUTING.md`](CONTRIBUTING.md) for development guidelines, commit message rules, and pre-commit setup.

---

## 📄 License

MIT — see [`LICENSE`](LICENSE) for details.
