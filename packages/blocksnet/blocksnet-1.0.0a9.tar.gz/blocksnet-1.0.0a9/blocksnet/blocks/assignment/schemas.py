import shapely
import pandas as pd
from pandera import parser
from pandera.typing import Series
from ...utils.validation import GdfSchema


class BlocksSchema(GdfSchema):
    @classmethod
    def _geometry_types(cls):
        return {shapely.Polygon}


class ObjectsSchema(GdfSchema):

    name: Series[str]

    # @parser('name')
    # def _parse_name(cls, name: pd.Series) -> pd.Series:
    #     return name.apply(str.lower)

    @classmethod
    def _geometry_types(cls):
        return {shapely.Polygon, shapely.MultiPolygon}


class FunctionalZonesSchema(GdfSchema):

    functional_zone: Series[str]

    @classmethod
    def _geometry_types(cls):
        return {shapely.Polygon, shapely.MultiPolygon}
