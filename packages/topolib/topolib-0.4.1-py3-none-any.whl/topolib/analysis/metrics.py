"""
Metrics module for network topology analysis.
"""

from typing import List, Any, Dict, Optional


from topolib.topology import Topology


class Metrics:
    """
    Provides static methods for computing metrics on network topologies.

    Todos los métodos reciben una instancia de Topology.

    Métodos
    -------
    node_degree(topology)
        Calcula el grado de cada nodo.
    link_length_stats(topology)
        Calcula estadísticas (min, max, avg) de las longitudes de los enlaces.
    connection_matrix(topology)
        Construye la matriz de adyacencia.
    """

    @staticmethod
    def node_degree(topology: "Topology") -> Dict[int, int]:
        """
        Calculates the degree of each node in the topology.

        :param topology: Instance of topolib.topology.topology.Topology.
        :type topology: topolib.topology.topology.Topology
        :return: Dictionary {node_id: degree}
        :rtype: dict[int, int]
        """
        degree = {n.id: 0 for n in topology.nodes}
        for link in topology.links:
            degree[link.source.id] += 1
            degree[link.target.id] += 1
        return degree

    @staticmethod
    def link_length_stats(topology: "Topology") -> Dict[str, Optional[float]]:
        """
        Calculates the minimum, maximum, and average link lengths.

        :param topology: Instance of topolib.topology.topology.Topology.
        :type topology: topolib.topology.topology.Topology
        :return: Dictionary with keys 'min', 'max', 'avg'.
        :rtype: dict[str, float | None]
        """
        lengths = [l.length for l in topology.links]
        if not lengths:
            return {"min": None, "max": None, "avg": None}
        return {
            "min": min(lengths),
            "max": max(lengths),
            "avg": sum(lengths) / len(lengths),
        }

    @staticmethod
    def connection_matrix(topology: "Topology") -> List[List[int]]:
        """
        Builds the adjacency matrix of the topology.

        :param topology: Instance of topolib.topology.topology.Topology.
        :type topology: topolib.topology.topology.Topology
        :return: Adjacency matrix (1 if connected, 0 otherwise).
        :rtype: list[list[int]]
        """
        id_to_idx = {n.id: i for i, n in enumerate(topology.nodes)}
        size = len(topology.nodes)
        matrix = [[0] * size for _ in range(size)]
        for link in topology.links:
            i = id_to_idx[link.source.id]
            j = id_to_idx[link.target.id]
            matrix[i][j] = 1
            matrix[j][i] = 1
        return matrix
