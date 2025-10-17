import pandas as pd
from .schemas import BlocksSchema
from .indicator import GeneralIndicator
from blocksnet.enums import LandUseCategory
from ..const import SQM_IN_SQKM, TOTAL_COLUMN
from ..utils import get_unique_parents


def _calculate_general_indicators(blocks_df: pd.DataFrame) -> dict[GeneralIndicator, float]:
    blocks_df = BlocksSchema(blocks_df)

    area = blocks_df["site_area"].sum()
    blocks_df["category"] = blocks_df["land_use"].apply(LandUseCategory.from_land_use)
    urban_area = blocks_df[blocks_df["category"] == LandUseCategory.URBAN]["site_area"].sum()
    urbanization = urban_area / area

    area = area / SQM_IN_SQKM

    return {GeneralIndicator.AREA: float(area), GeneralIndicator.URBANIZATION: float(urbanization)}


def calculate_general_indicators(blocks_df: pd.DataFrame) -> pd.DataFrame:
    parents = get_unique_parents(blocks_df)

    indicators = {}
    for parent in parents:
        indicators[parent] = _calculate_general_indicators(blocks_df[blocks_df.parent == parent])
    indicators[TOTAL_COLUMN] = _calculate_general_indicators(blocks_df)

    return pd.DataFrame.from_dict(indicators)
