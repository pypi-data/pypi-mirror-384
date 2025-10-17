import numpy as np
import pandas as pd
from .indicator import SocialIndicator
from tqdm import tqdm
from .schemas import ServiceTypesSchema
from .provision import calculate_provision
from .count import calculate_count
from .utils import cast_social_indicator
from ..utils import get_unique_parents
from ..const import TOTAL_COLUMN
from blocksnet.config import log_config
from blocksnet.analysis.services import services_count
from blocksnet.analysis.provision import provision_strong_total


def _calculate_count(
    counts_df: pd.DataFrame,
    indicator: SocialIndicator,
    service_types_df: pd.DataFrame | None,
    blocks_ids: list[int] | None = None,
) -> float | None:
    if blocks_ids is not None:
        counts_df = counts_df.loc[blocks_ids]
    return calculate_count(counts_df, indicator, service_types_df)


def _calculate_provision(prov_dfs: list[pd.DataFrame], blocks_ids: list[int] | None = None) -> float | None:
    if blocks_ids is not None:
        prov_dfs = [df.loc[blocks_ids] for df in prov_dfs]

    if len(prov_dfs) == 0:
        return None
    totals = [provision_strong_total(df) for df in prov_dfs]
    return float(np.mean(totals))


def calculate_social_indicators(
    blocks_df: pd.DataFrame,
    acc_mx: pd.DataFrame,
    dist_mx: pd.DataFrame | None,
    service_types_df: pd.DataFrame | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:

    parents = get_unique_parents(blocks_df)
    counts_df = services_count(blocks_df)
    if service_types_df is not None:
        service_types_df = ServiceTypesSchema(service_types_df)

    count_indicators = {p: {} for p in [*parents, TOTAL_COLUMN]}
    prov_indicators = {p: {} for p in [*parents, TOTAL_COLUMN]}

    for indicator in tqdm(list(SocialIndicator), disable=log_config.disable_tqdm):
        prov_dfs = calculate_provision(blocks_df, acc_mx, indicator, dist_mx, service_types_df)

        count_indicator, prov_indicator = cast_social_indicator(indicator)

        for parent in parents:
            blocks_ids = blocks_df[blocks_df.parent == parent].index.to_list()

            count = _calculate_count(counts_df, indicator, service_types_df, blocks_ids)
            count_indicators[parent][count_indicator] = count

            prov = _calculate_provision(prov_dfs, blocks_ids)
            prov_indicators[parent][prov_indicator] = prov

        count = calculate_count(counts_df, indicator, service_types_df)
        count_indicators[TOTAL_COLUMN][count_indicator] = count

        prov = _calculate_provision(prov_dfs)
        prov_indicators[TOTAL_COLUMN][prov_indicator] = prov

    return (pd.DataFrame.from_dict(count_indicators), pd.DataFrame.from_dict(prov_indicators))
