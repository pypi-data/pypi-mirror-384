from enum import unique
from ..indicator_enum import IndicatorEnum
from ..indicator_meta import IndicatorMeta


@unique
class SocialIndicator(IndicatorEnum):
    # education
    KINDERGARTEN = IndicatorMeta("kindergarten")
    SCHOOL = IndicatorMeta("school")
    COLLEGE = IndicatorMeta("college")
    UNIVERSITY = IndicatorMeta("university")
    EXTRACURRICULAR = IndicatorMeta("extracurricular")

    # healthcare
    HOSPITAL = IndicatorMeta("hospital")
    POLYCLINIC = IndicatorMeta("polyclinic")
    AMBULANCE = IndicatorMeta("ambulance")
    SANATORIUM = IndicatorMeta("sanatorium")
    SPECIAL_MEDICAL = IndicatorMeta("special_medical")
    PREVENTIVE_MEDICAL = IndicatorMeta("preventive_medical")
    PHARMACY = IndicatorMeta("pharmacy")

    # sports
    GYM = IndicatorMeta("gym")
    SWIMMING_POOL = IndicatorMeta("swimming_pool")
    PITCH = IndicatorMeta("pitch")
    STADIUM = IndicatorMeta("stadium")

    # social
    ORPHANAGE = IndicatorMeta("orphanage")
    SOCIAL_FACILITY = IndicatorMeta("social_facility")
    SOCIAL_SERVICE_CENTER = IndicatorMeta("social_service_center")

    # service
    POST = IndicatorMeta("post")
    BANK = IndicatorMeta("bank")
    MULTIFUNCTIONAL_CENTER = IndicatorMeta("multifunctional_center")

    # leisure
    LIBRARY = IndicatorMeta("library")
    MUSEUM = IndicatorMeta("museum")
    THEATRE = IndicatorMeta("theatre")
    CULTURAL_CENTER = IndicatorMeta("cultural_center")
    CINEMA = IndicatorMeta("cinema")
    CONCERT_HALL = IndicatorMeta("concert_hall")
    ICE_ARENA = IndicatorMeta("ice_arena")
    MALL = IndicatorMeta("mall")
    PARK = IndicatorMeta("park")
    BEACH = IndicatorMeta("beach")
    ECO_TRAIL = IndicatorMeta("eco_trail")

    # security
    FIRE_STATION = IndicatorMeta("fire_station")
    POLICE = IndicatorMeta("police")

    # tourism
    HOTEL = IndicatorMeta("hotel")
    HOSTEL = IndicatorMeta("hostel")
    TOURIST_BASE = IndicatorMeta("tourist_base")
    CATERING = IndicatorMeta("catering")


SocialCountIndicator = IndicatorEnum(
    "SocialCountIndicator",
    {e.name: e.value for e in SocialIndicator},
)
SocialProvisionIndicator = IndicatorEnum(
    "SocialProvisionIndicator",
    {e.name: e.value for e in SocialIndicator},
)
