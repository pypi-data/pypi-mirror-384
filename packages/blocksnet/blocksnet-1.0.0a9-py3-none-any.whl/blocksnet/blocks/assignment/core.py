import geopandas as gpd
import numpy as np
import pandas as pd
from loguru import logger
from .schemas import BlocksSchema, ObjectsSchema
from .utils import sjoin_intersections
from blocksnet.utils.validation import ensure_crs

LAND_USE_COLUMN = "land_use"
NAME_COLUMN = "name"
SHARE_COLUMN = "share"


def _calculate_shares(intersections_gdf: gpd.GeoDataFrame) -> pd.DataFrame:
    shares_df = intersections_gdf.groupby(["index_left", NAME_COLUMN]).agg({"share_left": "sum"})
    shares_df = shares_df.unstack(NAME_COLUMN, fill_value=0).droplevel(0, axis=1)
    return shares_df


def _choose_largest_share(shares_df: pd.DataFrame) -> pd.DataFrame:
    shares_df = shares_df.copy()

    names = shares_df.idxmax(axis=1)
    shares = shares_df.max(axis=1).replace(0, np.nan)

    shares_df[NAME_COLUMN] = names
    shares_df[SHARE_COLUMN] = shares

    shares_df.loc[shares_df[SHARE_COLUMN].isna(), NAME_COLUMN] = None

    return shares_df[[NAME_COLUMN, SHARE_COLUMN]]


def _get_names(objects_gdf: gpd.GeoDataFrame) -> list[str]:
    names = list(objects_gdf[NAME_COLUMN].unique())
    return names


def assign_objects(
    blocks_gdf: gpd.GeoDataFrame, objects_gdf: gpd.GeoDataFrame, names: list[str] | None = None
) -> gpd.GeoDataFrame:
    blocks_gdf = BlocksSchema(blocks_gdf)
    objects_gdf = ObjectsSchema(objects_gdf)
    ensure_crs(blocks_gdf, objects_gdf)

    names = names or _get_names(objects_gdf)
    blocks_gdf[names] = 0.0

    intersections_gdf = sjoin_intersections(blocks_gdf, objects_gdf)
    shares_df = _calculate_shares(intersections_gdf)
    blocks_gdf.loc[shares_df.index, shares_df.columns] = shares_df

    blocks_gdf[NAME_COLUMN] = None
    blocks_gdf[SHARE_COLUMN] = np.nan
    blocks_gdf.loc[shares_df.index, [NAME_COLUMN, SHARE_COLUMN]] = _choose_largest_share(shares_df)

    return blocks_gdf
