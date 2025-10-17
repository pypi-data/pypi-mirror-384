import numpy as np
import pandas as pd
import geopandas as gpd
from .schemas import BlocksSchema, BlocksAreaSchema, BlocksAccessibilitySchema
from ..const import SQM_IN_SQKM, M_IN_KM, MIN_IN_H
from blocksnet.enums import LandUse


def calculate_area(blocks_gdf: gpd.GeoDataFrame) -> float:
    blocks_df = BlocksAreaSchema(blocks_gdf)
    return float(blocks_df["site_area"].sum() / SQM_IN_SQKM)


def calculate_length(blocks_gdf: gpd.GeoDataFrame, roads_gdf: gpd.GeoDataFrame) -> float:
    from shapely import intersection

    blocks_gdf = BlocksSchema(blocks_gdf)
    blocks_geom = blocks_gdf.buffer(1).union_all()
    roads_geom = roads_gdf.to_crs(blocks_gdf.crs).union_all()
    intersection_geom = intersection(roads_geom, blocks_geom)
    return float(intersection_geom.length / M_IN_KM)


def calculate_connectivity(blocks_gdf: gpd.GeoDataFrame, accessibility_matrix: pd.DataFrame) -> float:

    residential_idx = blocks_gdf[blocks_gdf["land_use"] == LandUse.RESIDENTIAL].index
    if len(residential_idx) == 0:
        return np.nan
    acc_mx = accessibility_matrix.loc[residential_idx, residential_idx]
    return float(np.mean(acc_mx.to_numpy()) / MIN_IN_H)


def calculate_count(blocks_gdf: gpd.GeoDataFrame, name: str) -> tuple[int, pd.DataFrame]:
    column = f"count_{name}"
    if column in blocks_gdf:
        blocks_df = BlocksAccessibilitySchema(blocks_gdf.rename(columns={column: "count"}))
    else:
        raise RuntimeError(f"Column {column} not found in blocks")

    count = blocks_df["count"].sum()
    return int(count), blocks_df


def calculate_accessibility(counts_df: pd.DataFrame, accessibility_matrix: pd.DataFrame) -> float:

    residential_idx = counts_df[counts_df["land_use"] == LandUse.RESIDENTIAL].index
    services_idx = counts_df[counts_df["count"] > 0].index
    if len(residential_idx) == 0 or len(services_idx) == 0:
        return np.nan
    acc_mx = accessibility_matrix.loc[residential_idx, services_idx]
    accs = acc_mx.min(axis=1)
    return float(np.mean(accs.to_numpy()))
