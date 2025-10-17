import pandas as pd
from .indicator import SocialIndicator
from .utils import get_service_types, prepare_input
from blocksnet.config import service_types_config, log_config
from blocksnet.analysis.provision import competitive_provision


def _calculate_provision(
    blocks_df: pd.DataFrame,
    acc_mx: pd.DataFrame,
    service_type: str | int,
    dist_mx: pd.DataFrame | None,
    service_types_df: pd.DataFrame | None,
) -> pd.DataFrame | None:
    input = prepare_input(blocks_df, acc_mx, service_type, dist_mx, service_types_df)
    if any([v is None for v in input]):
        return None
    df, mx, demand, accessibility = input

    disable_tqdm = log_config.disable_tqdm
    logger_level = log_config.logger_level
    log_config.set_disable_tqdm(True)
    log_config.set_logger_level("ERROR")

    prov_df, _ = competitive_provision(df, mx, accessibility, demand)

    log_config.set_disable_tqdm(disable_tqdm)
    log_config.set_logger_level(logger_level)

    return prov_df


def calculate_provision(
    blocks_df: pd.DataFrame,
    acc_mx: pd.DataFrame,
    indicator: SocialIndicator,
    dist_mx: pd.DataFrame | None,
    service_types_df: pd.DataFrame | None,
) -> list[pd.DataFrame]:

    service_types = get_service_types(indicator, service_types_df)

    prov_dfs = []
    for service_type in service_types:
        prov_df = _calculate_provision(blocks_df, acc_mx, service_type, dist_mx, service_types_df)
        if prov_df is not None:
            prov_dfs.append(prov_df)

    return prov_dfs
