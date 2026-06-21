"""
OSM graph builder — downloads and caches road network graphs for Kenyan regions.
This is an optional heavy module; the API uses OSRM by default.
Use build_graph() when you need local networkx-based analysis (e.g. batch routing).
"""

import os
import pickle
from pathlib import Path

CACHE_DIR = Path(".cache/graphs")
CACHE_DIR.mkdir(parents=True, exist_ok=True)


def build_graph(place_name: str, network_type: str = "drive"):
    """
    Downloads or loads a cached OSM road graph for the given place.
    Returns a networkx MultiDiGraph with travel_time edge weights.
    Requires osmnx to be installed.
    """
    try:
        import osmnx as ox
    except ImportError:
        raise RuntimeError("osmnx is not installed. Run: pip install osmnx")

    cache_path = CACHE_DIR / f"{place_name.replace(' ', '_').lower()}.pkl"

    if cache_path.exists():
        with open(cache_path, "rb") as f:
            return pickle.load(f)

    graph = ox.graph_from_place(place_name, network_type=network_type)
    graph = ox.add_edge_speeds(graph)
    graph = ox.add_edge_travel_times(graph)

    with open(cache_path, "wb") as f:
        pickle.dump(graph, f)

    return graph


def route_on_graph(graph, origin_lat, origin_lon, dest_lat, dest_lon):
    """
    Finds the shortest path by travel_time on a local OSM graph.
    Returns list of (lat, lon) tuples representing the path.
    """
    try:
        import osmnx as ox
        import networkx as nx
    except ImportError:
        raise RuntimeError("osmnx and networkx are required for local graph routing.")

    orig_node = ox.distance.nearest_nodes(graph, origin_lon, origin_lat)
    dest_node = ox.distance.nearest_nodes(graph, dest_lon, dest_lat)
    path_nodes = nx.shortest_path(graph, orig_node, dest_node, weight="travel_time")

    coords = [(graph.nodes[n]["y"], graph.nodes[n]["x"]) for n in path_nodes]
    return coords
