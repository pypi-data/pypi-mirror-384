from enum import Enum
from .indicator_meta import IndicatorMeta


class IndicatorEnum(Enum):
    @property
    def meta(self) -> IndicatorMeta:
        return self.value

    def __str__(self):
        cls_name = self.__class__.__name__.removesuffix("Indicator").upper()
        repr = cls_name + " | " + self.meta.name.capitalize().replace("_", " ")
        if self.meta.unit is not None:
            repr = f"{repr} ({self.meta.unit})"
        return repr

    def __repr__(self):
        return self.__str__()
