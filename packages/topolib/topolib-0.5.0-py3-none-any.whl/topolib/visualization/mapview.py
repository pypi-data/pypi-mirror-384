"""
MapView class for visualizing network topologies.

This module provides visualization methods for Topology objects.
"""

from typing import Any
from topolib.topology import Topology
import matplotlib.pyplot as plt
import contextily as ctx
import geopandas as gpd
from shapely.geometry import Point


class MapView:
    """
    Provides visualization methods for Topology objects.
    """

    def __init__(self, topology: Topology) -> None:
        """
        Initialize MapView with a Topology object.
        :param topology: Topology object
        """
        self.topology = topology

    def show_map(self) -> None:
        """
        Show all nodes and links of the topology on an OpenStreetMap base using contextily and Matplotlib.
        The figure and plot title will be the topology name if available.
        """
        lons: list[float] = [node.longitude for node in self.topology.nodes]
        lats: list[float] = [node.latitude for node in self.topology.nodes]
        names: list[str] = [node.name for node in self.topology.nodes]
        gdf: gpd.GeoDataFrame = gpd.GeoDataFrame(
            {"name": names},
            geometry=[Point(x, y) for x, y in zip(lons, lats)],
            crs="EPSG:4326",
        )
        gdf = gdf.to_crs(epsg=3857)

        # Map node id to projected coordinates
        node_id_to_xy = {
            node.id: (pt.x, pt.y) for node, pt in zip(self.topology.nodes, gdf.geometry)
        }

        # Try to get topology name (from attribute or fallback)
        topo_name = getattr(self.topology, "name", None)
        if topo_name is None:
            # Try to get from dict if loaded from JSON
            topo_name = getattr(self.topology, "_name", None)
        if topo_name is None:
            topo_name = "Topology"

        fig, ax = plt.subplots(figsize=(10, 7))
        fig.suptitle(topo_name, fontsize=16)
        # Draw links as simple lines
        for link in getattr(self.topology, "links", []):
            src_id = getattr(link, "source").id
            tgt_id = getattr(link, "target").id
            if src_id in node_id_to_xy and tgt_id in node_id_to_xy:
                x0, y0 = node_id_to_xy[src_id]
                x1, y1 = node_id_to_xy[tgt_id]
                ax.plot(
                    [x0, x1], [y0, y1], color="gray", linewidth=1, alpha=0.7, zorder=2
                )
        # Draw nodes
        gdf.plot(ax=ax, color="blue", markersize=40, zorder=5)
        for x, y, name in zip(gdf.geometry.x, gdf.geometry.y, gdf["name"]):
            ax.text(x, y, name, fontsize=8, ha="right", va="bottom", color="black")
        ctx.add_basemap(ax, source=ctx.providers.OpenStreetMap.Mapnik)
        ax.set_axis_off()
        ax.set_title(f"Nodes and links ({topo_name})")
        plt.tight_layout()
        plt.show()
