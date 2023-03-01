import networkx as nx
import osmnx as ox
import pandas as pd
import geopandas as gpd
import time
import igraph as ig
import numpy as np
from shapely.geometry import Point, LineString


def compute_node_closeness(G_nx):
    
    weight = 'length'
    
    # create networkx graph
    osmids = list(G_nx.nodes)
    G_nx = nx.relabel.convert_node_labels_to_integers(G_nx)

    # give each node its original osmid as attribute since we relabeled them
    osmid_values = {k:v for k, v in zip(G_nx.nodes, osmids)}
    nx.set_node_attributes(G_nx, osmid_values, 'osmid')

    print("Convert to igraph ...")
    # convert networkx graph to igraph
    G_ig = ig.Graph(directed=True)
    G_ig.add_vertices(G_nx.nodes)
    G_ig.add_edges(G_nx.edges())
    G_ig.vs['osmid'] = osmids
    G_ig.es[weight] = list(nx.get_edge_attributes(G_nx, weight).values())
    assert len(G_nx.nodes()) == G_ig.vcount()
    assert len(G_nx.edges()) == G_ig.ecount()
    
    print("Calculating closeness ...")
    closeness1 = G_ig.closeness(vertices=None, mode='ALL', cutoff=None, weights=weight, normalized=True)
    
    print("Convert to dataframe closeness ...")
    gdf_nodes = ox.utils_graph.graph_to_gdfs(G_nx, nodes=True, edges=False, node_geometry=True, fill_edge_geometry=False)
    df_nodes = pd.DataFrame({'osmid': G_ig.vs["osmid"], 'node_closeness':closeness1})
    gdf_nodes = gdf_nodes.reset_index(drop=True)
    gdf_res = pd.merge(gdf_nodes, df_nodes, left_on='osmid', right_on='osmid', how='left')

    return gdf_res
    
    
def compute_edge_betweenness(G_nx):
    
    weight = 'length'
    
    # create networkx graph
    osmids = list(G_nx.edges)
    G_nx = nx.relabel.convert_node_labels_to_integers(G_nx)

    # give each edge its original osmid as attribute since we relabeled them
    osmid_values = {k:v for k, v in zip(G_nx.edges, osmids)}
    nx.set_edge_attributes(G_nx, osmid_values, 'osmid')
    
    print("Convert to igraph ...")
    # convert networkx graph to igraph
    G_ig = ig.Graph(directed=True)
    G_ig.add_vertices(G_nx.nodes)
    G_ig.add_edges(G_nx.edges())
    G_ig.es['osmid'] = osmids
    G_ig.es[weight] = list(nx.get_edge_attributes(G_nx, weight).values())
    assert len(G_nx.nodes()) == G_ig.vcount()
    assert len(G_nx.edges()) == G_ig.ecount()
    
    print("Calculating betweenness ...")
    betweenness = G_ig.edge_betweenness(directed=True, cutoff=None, weights=weight)
    
    print("Convert to dataframe betweenness ...")
    gdf_edges = ox.utils_graph.graph_to_gdfs(G_nx, nodes=False, edges=True, node_geometry=False, fill_edge_geometry=True)
    df_edges = pd.DataFrame({'osmid': G_ig.es["osmid"], 'edge_betweenness':betweenness})
    gdf_edges = gdf_edges.reset_index(drop=True)
    gdf_res = pd.merge(gdf_edges, df_edges, left_on='osmid', right_on='osmid', how='left')
    
    return gdf_res


def compute_edge_sinuosity(row):
    x, y = row.geometry.coords.xy
    start_pt = Point(x[0], y[0])
    end_pt = Point(x[-1], y[-1])
    straight_line = LineString((start_pt, end_pt))
    
    if straight_line.length:
        return row.geometry.length / straight_line.length
    else:
        return None