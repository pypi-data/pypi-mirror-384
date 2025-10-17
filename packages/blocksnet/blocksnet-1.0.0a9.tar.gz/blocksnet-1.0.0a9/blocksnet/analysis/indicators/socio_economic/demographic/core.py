import pandas as pd
from .schemas import BlocksSchema
from .indicator import DemographicIndicator
from ..const import SQM_IN_SQKM, TOTAL_COLUMN
from ..utils import get_unique_parents


def _calculate_demographic_indicators(blocks_df: pd.DataFrame) -> dict[DemographicIndicator, float]:
    blocks_df = BlocksSchema(blocks_df)
    area = blocks_df["site_area"].sum() / SQM_IN_SQKM
    population = blocks_df["population"].sum()
    density = population / area
    return {DemographicIndicator.POPULATION: int(population), DemographicIndicator.DENSITY: float(density)}


def calculate_demographic_indicators(blocks_df: pd.DataFrame) -> pd.DataFrame:
    parents = get_unique_parents(blocks_df)

    indicators = {}
    for parent in parents:
        indicators[parent] = _calculate_demographic_indicators(blocks_df[blocks_df.parent == parent])
    indicators[TOTAL_COLUMN] = _calculate_demographic_indicators(blocks_df)

    return pd.DataFrame.from_dict(indicators)
