import pandas as pd
import geopandas as gpd
import numpy as np
import networkx as nx
from blocksnet.enums.land_use import LandUse
from blocksnet.relations import validate_accessibility_matrix
from .schemas import BlocksSchema, BlocksAccessibilitySchema, validate_network
from .indicator import TransportIndicator
from . import utils
from ..const import M_IN_KM, SQM_IN_SQKM, MIN_IN_H
from ..const import SQM_IN_SQKM, TOTAL_COLUMN
from ..utils import get_unique_parents

SERVICE_TYPES_MAPPING = {
    "fuel": (TransportIndicator.FUEL_STATIONS_COUNT, TransportIndicator.AVERAGE_FUEL_STATION_ACCESSIBILITY),
    "train_station": (
        TransportIndicator.RAILWAY_STOPS_COUNT,
        TransportIndicator.AVERAGE_RAILWAY_STOP_ACCESSIBILITY,
    ),
    "aeroway_terminal": (
        TransportIndicator.AIRPORTS_COUNT,  # TransportIndicator.REGIONAL_AIRPORTS_COUNT],
        TransportIndicator.AVERAGE_AIRPORT_ACCESSIBILITY,  # TransportIndicator.AVERAGE_REGIONAL_AIRPORT_ACCESSIBILITY]
    ),
}


def _calculate_transport_indicators(
    blocks_gdf: gpd.GeoDataFrame, accessibility_matrix: pd.DataFrame, roads_gdf: gpd.GeoDataFrame
) -> dict[TransportIndicator, float]:

    validate_accessibility_matrix(accessibility_matrix, blocks_gdf)

    area = utils.calculate_area(blocks_gdf)
    length = utils.calculate_length(blocks_gdf, roads_gdf)
    density = length / area
    connectivity = utils.calculate_connectivity(blocks_gdf, accessibility_matrix)

    result = {
        TransportIndicator.ROAD_NETWORK_DENSITY: density,
        TransportIndicator.SETTLEMENTS_CONNECTIVITY: connectivity,
        TransportIndicator.ROAD_NETWORK_LENGTH: length,
    }

    for name, indicators in SERVICE_TYPES_MAPPING.items():
        count_indicator, accessibility_indicator = indicators
        count, df = utils.calculate_count(blocks_gdf, name)
        accessibility = utils.calculate_accessibility(df, accessibility_matrix)
        result[count_indicator] = count
        result[accessibility_indicator] = accessibility

    return result


def calculate_transport_indicators(
    blocks_gdf: gpd.GeoDataFrame, accessibility_matrix: pd.DataFrame, network: nx.Graph | gpd.GeoDataFrame
) -> pd.DataFrame:
    roads_gdf = validate_network(network)
    parents = get_unique_parents(blocks_gdf)

    indicators = {}
    for parent in parents:
        df = blocks_gdf[blocks_gdf.parent == parent].copy()
        acc_mx = accessibility_matrix.loc[df.index, df.index].copy()
        indicators[parent] = _calculate_transport_indicators(df, acc_mx, roads_gdf)
    indicators[TOTAL_COLUMN] = _calculate_transport_indicators(blocks_gdf, accessibility_matrix, roads_gdf)

    return pd.DataFrame.from_dict(indicators)
