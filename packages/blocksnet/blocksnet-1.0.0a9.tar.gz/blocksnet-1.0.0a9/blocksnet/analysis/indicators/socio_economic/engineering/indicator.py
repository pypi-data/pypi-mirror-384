from enum import unique
from ..indicator_enum import IndicatorEnum
from ..indicator_meta import IndicatorMeta


@unique
class EngineeringIndicator(IndicatorEnum):
    NON_GASIFIED_SETTLEMENTS = IndicatorMeta("non_gasified_settlements")
    INFRASTRUCTURE_OBJECT = IndicatorMeta("infrastructure_object")
    SUBSTATION = IndicatorMeta("substation")
    WATER_WORKS = IndicatorMeta("water_works")
    WASTEWATER_PLANT = IndicatorMeta("wastewater_plant")
    RESERVOIR = IndicatorMeta("reservoir")
    GAS_DISTRIBUTION = IndicatorMeta("gas_distribution")
