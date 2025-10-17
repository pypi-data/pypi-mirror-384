import pandas as pd
from .indicator import EngineeringIndicator
from blocksnet.analysis.services import services_count
from ..utils import get_unique_parents
from ..const import TOTAL_COLUMN

SKIP_INDICATORS = [
    EngineeringIndicator.NON_GASIFIED_SETTLEMENTS,
    EngineeringIndicator.INFRASTRUCTURE_OBJECT,
]


def _calculate_engineering_indicators(blocks_df: pd.DataFrame) -> dict[EngineeringIndicator, int]:
    blocks_df = services_count(blocks_df)

    count_indicators = [ind for ind in EngineeringIndicator if ind not in SKIP_INDICATORS]
    # count_columns = [f"count_{ind.meta.name}" for ind in count_indicators]
    # missing_columns = set(set(count_columns)).difference(blocks_df.columns)

    # if len(missing_columns) > 0:
    #     missing_str = str.join(", ", missing_columns)
    #     raise RuntimeError(f"Missing columns: {missing_str}")

    result = {}
    for indicator in count_indicators:
        column = f"count_{indicator.meta.name}"
        if column in blocks_df.columns:
            count = blocks_df[column].sum()
            result[indicator] = int(count)
        else:
            result[indicator] = None

    counts = [r for r in result.values() if r is not None]
    count = sum(counts) if len(counts) > 0 else None
    result[EngineeringIndicator.INFRASTRUCTURE_OBJECT] = count

    return result


def calculate_engineering_indicators(blocks_df: pd.DataFrame) -> pd.DataFrame:
    parents = get_unique_parents(blocks_df)

    indicators = {}
    for parent in parents:
        indicators[parent] = _calculate_engineering_indicators(blocks_df[blocks_df.parent == parent])
    indicators[TOTAL_COLUMN] = _calculate_engineering_indicators(blocks_df)

    return pd.DataFrame.from_dict(indicators)
