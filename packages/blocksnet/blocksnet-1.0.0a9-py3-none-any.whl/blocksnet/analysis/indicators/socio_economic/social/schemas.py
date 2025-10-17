from pandera import check, Field
from pandera.typing import Series
from .indicator import SocialIndicator
from blocksnet.utils.validation import DfSchema


class ServiceTypesSchema(DfSchema):
    indicator: Series = Field(nullable=True)

    meters: Series[float] = Field(ge=0, nullable=True)
    minutes: Series[float] = Field(ge=0, nullable=True)

    capacity: Series[float] = Field(ge=0, nullable=True)
    count: Series[float] = Field(ge=0, nullable=True)

    @check
    @classmethod
    def _check_indicator(cls, indicator):
        return indicator.apply(lambda i: True if i is None else isinstance(i, SocialIndicator))
