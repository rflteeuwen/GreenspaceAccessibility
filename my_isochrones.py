import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import LineString, shape, mapping, Point, Polygon, MultiPolygon
from shapely.ops import cascaded_union

import osmnx as ox
import networkx as nx


def set_travel_costs(G, polygon):
    
    for u, v, k, data in G.edges(data=True, keys=True):
        # set edges within this greenspace to travel cost 0
        if data['geometry'].intersects(polygon):
            data['cost'] = 0
        else:
            data['cost'] = data['length']
            
    return G


def get_start_nodes(G, polygon, local_crs):
    
    start_nodes = []
    
    edges = ox.utils_graph.graph_to_gdfs(G, nodes=False, edges=True).to_crs(local_crs)
    nodes = ox.utils_graph.graph_to_gdfs(G, nodes=True, edges=False).to_crs(local_crs)
    
    zone = gpd.clip(edges, polygon).geometry.buffer(1).unary_union
    
    if zone:
        
        if zone.geom_type == 'MultiPolygon':
            for sub_zone in gpd.geoseries.GeoSeries([geom for geom in zone.geoms]):
                intersecting = nodes[nodes.intersects(sub_zone)].index
                if len(intersecting)>0:
                    start_nodes.append(intersecting[0])
        elif zone.geom_type == 'Polygon':
            intersecting = nodes[nodes.intersects(zone)].index
            if len(intersecting)>0:
                start_nodes.append(intersecting[0])

    return start_nodes


def get_iso_polys(G, start_node, trip_distance, edge_buff=25, node_buff=50, infill=False):
    
    isochrone_polys = []

    subgraph = nx.ego_graph(G, start_node, radius=trip_distance, distance='cost')

    node_points = [Point((data['x'], data['y'])) for node, data in subgraph.nodes(data=True)]
    nodes_gdf = gpd.GeoDataFrame({'id': subgraph.nodes()}, geometry=node_points)
    nodes_gdf = nodes_gdf.set_index('id')

    edge_lines = []
    for n_fr, n_to in subgraph.edges():
        f = nodes_gdf.loc[n_fr].geometry
        t = nodes_gdf.loc[n_to].geometry
        edge_lookup = G.get_edge_data(n_fr, n_to)[0].get('geometry',  LineString([f,t]))
        edge_lines.append(edge_lookup)

    n = nodes_gdf.buffer(node_buff).geometry
    e = gpd.GeoSeries(edge_lines).buffer(edge_buff).geometry
    all_gs = list(n) + list(e)
    new_iso = gpd.GeoSeries(all_gs).unary_union

    # try to fill in surrounded areas so shapes will appear solid and blocks without white space inside them
    if not new_iso.is_empty:
        if infill:
            new_iso = Polygon(new_iso.exterior)
        isochrone_polys.append(new_iso)
        
    return new_iso


def get_isochrones(G, gdf, trip_distances, local_crs):

    G = ox.project_graph(G, to_crs=local_crs)

    for index, row in gdf.iterrows():

        G = set_travel_costs(G, row.geometry)
        start_nodes = get_start_nodes(G, row.geometry, local_crs)
        
        for i, trip_distance in enumerate(trip_distances, start=1):
            trip_polys = [row.geometry]
            
            for start_node in start_nodes:
                poly = get_iso_polys(
                    G, start_node, trip_distance,
                    edge_buff=25, node_buff=0, infill=True)
                trip_polys.append(poly)
            polys_union = gpd.geoseries.GeoSeries(trip_polys).unary_union

            col = 'geom_iso_{}'.format(str(trip_distance))
            gdf.loc[index, col] = polys_union