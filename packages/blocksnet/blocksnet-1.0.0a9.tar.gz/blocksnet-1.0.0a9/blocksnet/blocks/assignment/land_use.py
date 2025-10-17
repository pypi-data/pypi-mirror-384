import geopandas as gpd
from loguru import logger
from blocksnet.enums import LandUse
from .schemas import FunctionalZonesSchema
from .core import assign_objects, NAME_COLUMN

LAND_USE_COLUMN = "land_use"


def _preprocess_functional_zones(functional_zones_gdf: gpd.GeoDataFrame, rules: dict[str, LandUse]) -> gpd.GeoDataFrame:
    functional_zones_gdf = FunctionalZonesSchema(functional_zones_gdf)

    gdf_fz = set(functional_zones_gdf["functional_zone"].unique())
    rules_fz = set(rules.keys())
    unknown_fz = gdf_fz - rules_fz
    if len(unknown_fz) > 0:
        logger.warning(f'Functional zones not in rules: {str.join(", ", unknown_fz)}')

    functional_zones_gdf[NAME_COLUMN] = functional_zones_gdf.functional_zone.map(rules)
    functional_zones_gdf = functional_zones_gdf[~functional_zones_gdf[NAME_COLUMN].isna()]
    functional_zones_gdf[NAME_COLUMN] = functional_zones_gdf[NAME_COLUMN].apply(lambda lu: lu.value)

    return functional_zones_gdf


def assign_land_use(
    blocks_gdf: gpd.GeoDataFrame,
    functional_zones_gdf: gpd.GeoDataFrame,
    rules: dict[str, LandUse],
) -> gpd.GeoDataFrame:
    functional_zones_gdf = _preprocess_functional_zones(functional_zones_gdf, rules)
    names = [lu.value for lu in LandUse]
    assign_gdf = assign_objects(blocks_gdf, functional_zones_gdf, names)

    assign_gdf[NAME_COLUMN] = assign_gdf[NAME_COLUMN].apply(lambda lu: lu if lu is None else LandUse(lu))

    return assign_gdf.rename(columns={NAME_COLUMN: LAND_USE_COLUMN})
