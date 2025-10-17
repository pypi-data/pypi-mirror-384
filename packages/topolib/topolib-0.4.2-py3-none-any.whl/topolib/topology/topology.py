"""
Topology class for optical network topologies.

This module defines the Topology class, representing a network topology with nodes and links,
and providing an adjacency matrix using numpy.

This file uses NetworkX (BSD 3-Clause License):
https://github.com/networkx/networkx/blob/main/LICENSE.txt
"""

from typing import List, Dict, Any, Optional
import numpy as np
import networkx as nx
from topolib.elements.node import Node
from topolib.elements.link import Link


class Topology:
    """
    Represents a network topology with nodes and links.

    :param nodes: Initial list of nodes (optional).
    :type nodes: list[topolib.elements.node.Node] or None
    :param links: Initial list of links (optional).
    :type links: list[topolib.elements.link.Link] or None

    :ivar nodes: List of nodes in the topology.
    :vartype nodes: list[Node]
    :ivar links: List of links in the topology.
    :vartype links: list[Link]

    **Examples**
        >>> from topolib.elements.node import Node
        >>> from topolib.elements.link import Link
        >>> from topolib.topology import Topology
        >>> n1 = Node(1, "A", 0.0, 0.0)
        >>> n2 = Node(2, "B", 1.0, 1.0)
        >>> l1 = Link(1, n1, n2, 10.0)
        >>> topo = Topology(nodes=[n1, n2], links=[l1])
        >>> topo.adjacency_matrix()
        array([[0, 1],
               [1, 0]])
    """

    def __init__(
        self,
        nodes: Optional[List[Node]] = None,
        links: Optional[List[Link]] = None,
        name: Optional[str] = None,
    ):
        """
        Initialize a Topology object.

        :param nodes: Initial list of nodes (optional).
        :type nodes: list[topolib.elements.node.Node] or None
        :param links: Initial list of links (optional).
        :type links: list[topolib.elements.link.Link] or None
        :param name: Name of the topology (optional).
        :type name: str or None
        """
        self.nodes = nodes if nodes is not None else []
        self.links = links if links is not None else []
        self.name = name
        # Internal NetworkX graph for algorithms and visualization
        self._graph = nx.Graph()
        for node in self.nodes:
            self._graph.add_node(node.id, node=node)
        for link in self.links:
            self._graph.add_edge(link.source.id, link.target.id, link=link)

    @classmethod
    def from_json(cls, json_path: str) -> "Topology":
        """
        Create a Topology object from a JSON file.

        :param json_path: Path to the JSON file containing the topology.
        :type json_path: str
        :return: Topology instance loaded from the file.
        :rtype: Topology
        """
        import json
        from topolib.elements.node import Node
        from topolib.elements.link import Link

        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        nodes = [
            Node(
                n["id"],
                n["name"],
                n["latitude"],
                n["longitude"],
                n.get("weight", 0),
                n.get("pop", 0),
                n.get("dc", n.get("DC", 0)),
                n.get("ixp", n.get("IXP", 0)),
            )
            for n in data["nodes"]
        ]
        # Crear un dict para mapear id a Node
        node_dict = {n.id: n for n in nodes}
        links = [
            Link(l["id"], node_dict[l["src"]], node_dict[l["dst"]], l["length"])
            for l in data["links"]
        ]
        name = data.get("name", None)
        return cls(nodes=nodes, links=links, name=name)

    def add_node(self, node: Node) -> None:
        """
        Add a node to the topology.

        :param node: Node to add.
        :type node: Node
        """
        self.nodes.append(node)
        self._graph.add_node(node.id, node=node)

    def add_link(self, link: Link) -> None:
        """
        Add a link to the topology.

        :param link: Link to add.
        :type link: Link
        """
        self.links.append(link)
        self._graph.add_edge(link.source.id, link.target.id, link=link)

    def remove_node(self, node_id: int) -> None:
        """
        Remove a node and all its links by node id.

        :param node_id: ID of the node to remove.
        :type node_id: int
        """
        self.nodes = [n for n in self.nodes if n.id != node_id]
        self.links = [
            l for l in self.links if l.source.id != node_id and l.target.id != node_id
        ]
        self._graph.remove_node(node_id)

    def remove_link(self, link_id: int) -> None:
        """
        Remove a link by its id.

        :param link_id: ID of the link to remove.
        :type link_id: int
        """
        # Find the link and remove from graph
        link = next((l for l in self.links if l.id == link_id), None)
        if link:
            self._graph.remove_edge(link.source.id, link.target.id)
        self.links = [l for l in self.links if l.id != link_id]

    def adjacency_matrix(self) -> np.ndarray:
        """
        Return the adjacency matrix of the topology as a numpy array.

        :return: Adjacency matrix (1 if connected, 0 otherwise).
        :rtype: numpy.ndarray

        **Example**
            >>> topo.adjacency_matrix()
            array([[0, 1],
                   [1, 0]])
        """
        # Usa NetworkX para obtener la matriz de adyacencia
        if not self.nodes:
            return np.zeros((0, 0), dtype=int)
        node_ids = [n.id for n in self.nodes]
        mat = nx.to_numpy_array(self._graph, nodelist=node_ids, dtype=int)
        return mat
