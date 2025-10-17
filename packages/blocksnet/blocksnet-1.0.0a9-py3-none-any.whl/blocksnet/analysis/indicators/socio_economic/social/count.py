import pandas as pd
from .indicator import SocialIndicator
from .utils import get_service_types


def calculate_count(
    counts_df: pd.DataFrame, indicator: SocialIndicator, service_types_df: pd.DataFrame | None
) -> float | None:

    service_types = get_service_types(indicator, service_types_df)

    columns = [f"count_{st}" for st in service_types]

    total_count = None
    for column in columns:
        if column in counts_df.columns:
            column_count = counts_df[column].sum()
            if total_count is None:
                total_count = column_count
            else:
                total_count += column_count

    return total_count
