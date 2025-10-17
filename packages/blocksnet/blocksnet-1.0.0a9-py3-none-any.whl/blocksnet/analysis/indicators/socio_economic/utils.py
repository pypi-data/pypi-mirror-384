from typing import Hashable
import pandas as pd

PARENT_COLUMN = "parent"


def get_unique_parents(blocks_df: pd.DataFrame) -> list[Hashable]:
    if PARENT_COLUMN in blocks_df:
        parents = blocks_df[PARENT_COLUMN].unique()
        return [p for p in parents if (p is not None and isinstance(p, Hashable))]
    return []
