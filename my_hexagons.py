import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import Polygon


def get_hex_grid(extent, id_col, radius, intersect=True):
    
    # modified version of https://sabrinadchan.github.io/data-blog/building-a-hexagonal-cartogram.html
    
    # radius = edge length

    # cover whole extent
    xmin = extent.total_bounds[0] - radius
    ymin = extent.total_bounds[1] - radius
    xmax = extent.total_bounds[2] + radius
    ymax = extent.total_bounds[3] + radius

    # alpha angle and nr of cols and rows
    a = np.sin(np.pi / 3)
    cols = np.arange(np.floor(xmin), np.ceil(xmax), 3 * radius)
    rows = np.arange(np.floor(ymin) / a, np.ceil(ymax) / a, radius)

    # create the hexagons
    hexagons = []
    for x in cols:
        for i, y in enumerate(rows):
            if (i % 2 == 0):
                x0 = x
            else:
                x0 = x + 1.5 * radius

            hexagons.append(Polygon([
                (x0, y * a),
                (x0 + radius, y * a),
                (x0 + (1.5 * radius), (y + radius) * a),
                (x0 + radius, (y + (2 * radius)) * a),
                (x0, (y + (2 * radius)) * a),
                (x0 - (0.5 * radius), (y + radius) * a),
            ]))

    # set geometry, index, crs
    grid = gpd.GeoDataFrame({'geometry': hexagons})
    grid = grid.reset_index().rename(columns={"index": "hex_id"})
    grid.crs = extent.crs
    
    # if intersect = True, keep only those grid cells that intersect with the area of interest
    if intersect:
        intersected = gpd.overlay(extent, grid, how='intersection')
        intersected["area_"] = intersected.area
        max_intersection = intersected.loc[intersected.index.isin(intersected.groupby(["hex_id"]).area_.idxmax())]
        tagged_grid = grid.merge(max_intersection[["hex_id", id_col]], how="left", on="hex_id")
        grid = tagged_grid[tagged_grid[id_col].notnull()]      
    
    return grid