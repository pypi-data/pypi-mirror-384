from pandera import Field
from pandera.typing import Series
from shapely.geometry import LineString, MultiLineString, Polygon
from shapely.geometry.base import BaseGeometry
from blocksnet.utils.validation import DfSchema, GdfSchema, LandUseSchema
import networkx as nx
import geopandas as gpd


class BlocksSchema(GdfSchema):
    @classmethod
    def _geometry_types(cls) -> set[type[BaseGeometry]]:
        return {Polygon}


class BlocksAreaSchema(DfSchema):
    site_area: Series[float] = Field(ge=0)


class BlocksAccessibilitySchema(LandUseSchema):
    count: Series[int] = Field(ge=0)


class NetworkSchema(GdfSchema):
    @classmethod
    def _geometry_types(cls) -> set[type[BaseGeometry]]:
        return {LineString, MultiLineString}


def validate_network(network: nx.Graph | gpd.GeoDataFrame) -> gpd.GeoDataFrame:

    from blocksnet.relations import accessibility_graph_to_gdfs

    if isinstance(network, nx.Graph):
        _, edges_df = accessibility_graph_to_gdfs(network)
        network_gdf = NetworkSchema(edges_df.reset_index(drop=True))
    elif isinstance(network, gpd.GeoDataFrame):
        network_gdf = NetworkSchema(network)
    else:
        raise TypeError("Network must be an instance of nx.Graph or gpd.GeoDataFrame")

    return network_gdf
