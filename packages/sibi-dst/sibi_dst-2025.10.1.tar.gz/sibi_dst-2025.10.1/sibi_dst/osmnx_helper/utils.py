from __future__ import annotations

import math
import os
import pickle
from urllib.parse import urlencode, urlsplit, urlunsplit

import folium
import geopandas as gpd
import numpy as np
import osmnx as ox
from geopy.distance import geodesic

from typing import Optional
from fsspec.core import url_to_fs

class PBFHandler:
    """
    Build/load OSMnx graph + nodes/edges; persist as pickle via fsspec.
    """

    def __init__(self, **kwargs):
        self.graph = None
        self.nodes: Optional[gpd.GeoDataFrame] = None
        self.edges: Optional[gpd.GeoDataFrame] = None

        self.rebuild: bool = kwargs.setdefault("rebuild", False)
        self.verbose: bool = kwargs.setdefault("verbose", False)
        self.place: str = kwargs.setdefault("place", "Costa Rica")
        self.network_type: str = kwargs.setdefault("network_type", "all")
        base_url: str = kwargs.setdefault("data_path", "osmnx_data/pbf_files")
        prefix: str = kwargs.setdefault("files_prefix", "costa-rica-").rstrip("-") + "-"

        # Allow passing an fsspec instance directly
        fs = kwargs.get("fs")
        if fs is not None:
            self.fs = fs
            self.base = base_url.rstrip("/")
        else:
            self.fs, self.base = url_to_fs(base_url)

        self.fs.mkdirs(self.base, exist_ok=True)

        self.graph_file = f"{self.base.rstrip('/')}/{prefix}graph.pkl"
        self.node_file = f"{self.base.rstrip('/')}/{prefix}nodes.pkl"
        self.edge_file = f"{self.base.rstrip('/')}/{prefix}edges.pkl"

        if self.verbose:
            print(f"[PBFHandler] base={self.base}")
            print(f"  graph={self.graph_file}")
            print(f"  nodes={self.node_file}")
            print(f"  edges={self.edge_file}")

    # ---------- public API ----------
    def load(self) -> None:
        if self.verbose:
            print("[PBFHandler] load()")

        if self.rebuild:
            self._delete_artifacts()

        if not self._artifacts_exist():
            self.process_pbf()
            self.save_to_pickle()
        else:
            self.load_from_pickle()

    def process_pbf(self) -> None:
        if self.verbose:
            print(f"[PBFHandler] processing: {self.place}")
        self.graph = ox.graph_from_place(self.place, network_type=self.network_type)
        self.nodes, self.edges = ox.graph_to_gdfs(self.graph)

    def save_to_pickle(self) -> None:
        if self.verbose:
            print("[PBFHandler] saving via fsspec")
        for path, obj in {
            self.graph_file: self.graph,
            self.node_file: self.nodes,
            self.edge_file: self.edges,
        }.items():
            if obj is not None:
                with self.fs.open(path, "wb") as f:
                    pickle.dump(obj, f, protocol=pickle.HIGHEST_PROTOCOL)

    def load_from_pickle(self) -> None:
        if self.verbose:
            print("[PBFHandler] loading via fsspec")
        self.graph = self._load_pickle(self.graph_file)
        self.nodes = self._load_pickle(self.node_file)
        self.edges = self._load_pickle(self.edge_file)

    # ---------- helpers ----------
    def _artifacts_exist(self) -> bool:
        return all(self.fs.exists(p) for p in (self.graph_file, self.node_file, self.edge_file))

    def _delete_artifacts(self) -> None:
        if self.verbose:
            print("[PBFHandler] deleting artifacts (rebuild=True)")
        for p in (self.graph_file, self.node_file, self.edge_file):
            if self.fs.exists(p):
                try:
                    self.fs.rm_file(p)
                except Exception:
                    self.fs.rm(p)

    def _load_pickle(self, path: str):
        with self.fs.open(path, "rb") as f:
            return pickle.load(f)


def get_bounding_box_from_points(gps_points, margin=0.001):
    """
    Calculates a bounding box from a list of GPS points, with an optional margin added
    to expand the bounding box in all directions. The function iterates over the GPS
    points to determine the maximum and minimum latitude and longitude values, then
    applies the specified margin to calculate the bounding box's boundaries.

    :param gps_points: A list of GPS points, where each point is represented as a tuple
        containing a latitude and a longitude (latitude, longitude).
    :type gps_points: list[tuple[float, float]]
    :param margin: An optional margin value to expand the bounding box in all directions.
        Default value is 0.001.
    :type margin: float
    :return: A tuple containing the bounding box boundaries in the following order:
        north (maximum latitude), south (minimum latitude), east (maximum longitude),
        and west (minimum longitude), each adjusted with the margin.
    :rtype: tuple[float, float, float, float]
    """
    latitudes = [point[0] for point in gps_points]
    longitudes = [point[1] for point in gps_points]

    north = max(latitudes) + margin
    south = min(latitudes) - margin
    east = max(longitudes) + margin
    west = min(longitudes) - margin

    return north, south, east, west


def add_arrows(map_object, locations, color, n_arrows):
    """
    Adds directional arrows to a map object to indicate paths or flows along a polyline
    defined by the given locations.

    The function computes directional arrows based on the locations list, places them
    along the defined path at intervals determined by the number of arrows, and adds
    these arrows to the specified `map_object`.

    .. note::
        The function works optimally when the number of locations is greater than two.

    :param map_object: The folium map object to which the directional arrows will be added.
    :param locations: A list containing tuples of latitude and longitude values that define
        the polyline. Each tuple represents a geographic point.
    :type locations: list[tuple[float, float]]
    :param color: The color to be used for the directional arrows.
    :type color: str
    :param n_arrows: The number of arrows to be drawn along the path.
    :type n_arrows: int
    :return: The modified folium map object containing the added arrows.
    :rtype: folium.Map
    """
    # Get the number of locations
    n = len(locations)

    # If there are more than two points...
    if n > 2:
        # Add arrows along the path
        for i in range(0, n - 1, n // n_arrows):
            # Get the start and end point for this segment
            start, end = locations[i], locations[i + 1]

            # Calculate the direction in which to place the arrow
            rotation = -np.arctan2((end[1] - start[1]), (end[0] - start[0])) * 180 / np.pi

            folium.RegularPolygonMarker(location=end,
                                        fill_color=color,
                                        number_of_sides=2,
                                        radius=6,
                                        rotation=rotation).add_to(map_object)
    return map_object


def extract_subgraph(G, north, south, east, west):
    """
    Extracts a subgraph from the input graph `G` within a specified bounding box. The bounding
    box is defined by its north, south, east, and west coordinates. The function identifies
    nodes from the graph that lie within this bounding box and creates a subgraph containing
    only these nodes and their corresponding edges.

    :param G: The input graph representing the original main graph.
    :type G: networkx.Graph
    :param north: The northern latitude that defines the upper boundary of the bounding box.
    :type north: float
    :param south: The southern latitude that defines the lower boundary of the bounding box.
    :type south: float
    :param east: The eastern longitude that defines the right boundary of the bounding box.
    :type east: float
    :param west: The western longitude that defines the left boundary of the bounding box.
    :type west: float
    :return: A subgraph extracted from the input graph `G` containing nodes and edges within
             the specified bounding box.
    :rtype: networkx.Graph
    """
    # Create a bounding box polygon
    # from osmnx v2 this is how it is done
    if ox.__version__ >= '2.0':
        bbox_poly = gpd.GeoSeries([ox.utils_geo.bbox_to_poly(bbox=(west, south, east, north))])
    else:
        bbox_poly = gpd.GeoSeries([ox.utils_geo.bbox_to_poly(north, south, east, west)])

    # Get nodes GeoDataFrame
    nodes_gdf = ox.graph_to_gdfs(G, nodes=True, edges=False)

    # Find nodes within the bounding box
    nodes_within_bbox = nodes_gdf[nodes_gdf.geometry.within(bbox_poly.geometry.unary_union)]

    # Create subgraph
    subgraph = G.subgraph(nodes_within_bbox.index)

    return subgraph


def get_distance_between_points(point_a, point_b, unit='km'):
    """
    Calculate the geographical distance between two points on Earth.

    This function computes the distance between two points on the Earth's surface
    specified in their geographical coordinates (latitude, longitude). The calculation
    employs the geodesic distance, which represents the shortest distance between
    two points on the Earth's surface. The distance can be returned in different units of
    measurement depending on the provided parameter.

    :param point_a: A tuple representing the latitude and longitude of the first
        point in decimal degrees (e.g., (latitude, longitude)). Must be a tuple of
        two float values.
    :param point_b: A tuple representing the latitude and longitude of the second
        point in decimal degrees (e.g., (latitude, longitude)). Must be a tuple of
        two float values.
    :param unit: A string value representing the unit of the calculated distance. Can be
        'km' for kilometers (default), 'm' for meters, or 'mi' for miles.
    :return: A float value of the distance between the two points in the specified unit.
        Returns 0 if the input validation fails or the specified unit is invalid.
    """
    if not isinstance(point_a, tuple) or len(point_a) != 2:
        return 0
    if not all(isinstance(x, float) and not math.isnan(x) for x in point_a):
        return 0
    if not isinstance(point_b, tuple) or len(point_b) != 2:
        return 0
    if not all(isinstance(x, float) and not math.isnan(x) for x in point_b):
        return 0
    distance = geodesic(point_a, point_b)
    if unit == 'km':
        return distance.kilometers
    elif unit == 'm':
        return distance.meters
    elif unit == 'mi':
        return distance.miles
    else:
        return 0


tile_options = {
    "OpenStreetMap": "OpenStreetMap",
    "CartoDB": "cartodbpositron",
    "CartoDB Voyager": "cartodbvoyager"
}


def attach_supported_tiles(map_object, default_tile="OpenStreetMap"):
    """
    Attaches supported tile layers to a given folium map object, excluding the
    default tile layer, to provide layer selection functionality in the map.

    This function allows dynamic addition of multiple tile layers to the map
    object while avoiding duplication of the default tile. By filtering out the
    default tile, it prevents redundancy and ensures a cleaner map interface.

    :param map_object: The folium map object to which the tile layers will be added.
        It must be an instance of Folium's Map class or a compatible map object.
    :param default_tile: The name of the default tile layer to exclude from the
        list of tiles added to the map. If not specified, defaults to 'OpenStreetMap'.
    :return: None. The function modifies the provided map object in place.
    """
    # Normalize the default tile name to lowercase for comparison
    normalized_default_tile = default_tile.lower()

    # Filter out the default tile layer from the options to avoid duplication
    tile_options_filtered = {k: v for k, v in tile_options.items() if v.lower() != normalized_default_tile}

    for tile, description in tile_options_filtered.items():
        folium.TileLayer(name=tile, tiles=description, show=False).add_to(map_object)


def get_graph(**options):
    """
    Generates and returns a graph along with its nodes and edges based on the
    provided options. The function initializes a PBFHandler instance with the
    given options, processes any data required, and retrieves the resulting
    graph structure.

    :param options: Variable-length keyword arguments passed to initialize the
                    PBFHandler instance. These parameters play a role in
                    determining how the graph data is processed and structured.
    :return: Returns a tuple containing three elements:
             - The generated graph object
             - The list or collection of nodes within the graph
             - The list or collection of edges that describe relationships
               between nodes in the graph
    """
    if not options:
        raise ValueError("No options provided to PBFHandler for graph creation.")
    handler = PBFHandler(**options)
    handler.load()
    return handler.graph, handler.nodes, handler.edges


def add_query_params(url, params):
    """
    Update the query parameters of a given URL with new parameters.

    This function takes a URL and a dictionary of parameters, merges these
    parameters with the existing parameters in the URL, and returns a new URL
    with updated query parameters.

    :param url: The original URL whose query parameters are to be updated,
        including the scheme, netloc, path, and optional query string and fragment.
    :type url: str
    :param params: A dictionary containing the new parameters to be added or updated
        in the query string of the given URL.
    :type params: dict
    :return: A new URL with updated query parameters after merging the original
        and new parameters.
    :rtype: str
    """
    # Parse the original URL
    url_components = urlsplit(url)

    # Parse original query parameters and update with new params
    original_params = dict([tuple(pair.split('=')) for pair in url_components.query.split('&') if pair])
    original_params.update(params)

    # Construct the new query string
    new_query_string = urlencode(original_params)

    # Construct the new URL
    new_url = urlunsplit((
        url_components.scheme,
        url_components.netloc,
        url_components.path,
        new_query_string,
        url_components.fragment
    ))

    return new_url


