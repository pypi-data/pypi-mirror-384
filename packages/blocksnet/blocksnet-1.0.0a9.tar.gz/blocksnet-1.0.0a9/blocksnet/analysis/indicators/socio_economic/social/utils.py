import pandas as pd
from .indicator import SocialIndicator, SocialCountIndicator, SocialProvisionIndicator
from blocksnet.config import service_types_config


def get_service_types(indicator: SocialIndicator, service_types_df: pd.DataFrame | None) -> list[int | str]:

    if indicator == SocialIndicator.CATERING:
        return ["cafe", "bar", "restaurant", "bakery"]

    service_type = indicator.meta.name
    if service_type in service_types_config:
        return [service_type]

    if service_types_df is not None:
        service_types_df = service_types_df[service_types_df.indicator == indicator]
        return list(service_types_df.index)

    return []


def _choose_accessibility(
    service_type_row: pd.Series, acc_mx: pd.DataFrame, dist_mx: pd.DataFrame | None
) -> tuple[float | None, pd.DataFrame | None]:
    time = service_type_row["minutes"]
    meters = service_type_row["meters"]
    if pd.notna(time):
        return float(time), acc_mx
    if pd.notna(meters):
        if dist_mx is None:
            return None, None
        return float(meters), dist_mx
    return None, None


def _choose_demand(service_type_row: pd.Series, blocks_df: pd.DataFrame) -> tuple[float | None, pd.DataFrame | None]:
    service_type_id = service_type_row.name
    count = service_type_row["count"]
    capacity = service_type_row["capacity"]

    if pd.notna(count):  # умножаем на 100 для придания большей точности, потому что задача целочисленная
        column = f"count_{service_type_id}"
        if not column in blocks_df:
            return None, None
        df = blocks_df.rename(
            columns={
                column: "capacity",
            }
        )[["population", "capacity"]]
        df["capacity"] *= 100
        return float(count) * 100, df

    if pd.notna(capacity):
        column = f"capacity_{service_type_id}"
        if not column in blocks_df:
            return None, None
        df = blocks_df.rename(
            columns={
                column: "capacity",
            }
        )[["population", "capacity"]]
        return float(capacity), df

    return None, None


def prepare_input(
    blocks_df: pd.DataFrame,
    acc_mx: pd.DataFrame,
    service_type: str | int,
    dist_mx: pd.DataFrame | None,
    service_types_df: pd.DataFrame | None,
) -> tuple[pd.DataFrame | None, pd.DataFrame | None, float | None, float | None]:
    blocks_df = blocks_df.copy()

    df = None
    mx = None
    demand = None
    accessibility = None

    if str(service_type) in service_types_config:
        _, demand, accessibility = service_types_config[service_type].values()
        df = blocks_df.rename(columns={f"capacity_{service_type}": "capacity"})
        mx = acc_mx
    elif service_types_df is not None:

        service_type_row = service_types_df.loc[service_type]
        accessibility, mx = _choose_accessibility(service_type_row, acc_mx, dist_mx)
        demand, df = _choose_demand(service_type_row, blocks_df)

    return df, mx, demand, accessibility


def cast_social_indicator(indicator: SocialIndicator) -> tuple:

    from typing import cast

    name = indicator.name
    return SocialCountIndicator[name], SocialProvisionIndicator[name]
