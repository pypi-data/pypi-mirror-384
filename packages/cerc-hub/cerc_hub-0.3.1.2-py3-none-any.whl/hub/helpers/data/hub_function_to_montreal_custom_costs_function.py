"""
Dictionaries module for hub function to Montreal custom costs function
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2022 Concordia CERC group
Project Coder Pilar Monsalvete Alvarez de Uribarri pilar.monsalvete@concordia.ca
"""

import hub.helpers.constants as cte


class HubFunctionToMontrealCustomCostsFunction:
  """
  Hub function to montreal custom cost function
  """

  def __init__(self):
    self._dictionary = {
      cte.RESIDENTIAL: 'residential',
      cte.SINGLE_FAMILY_HOUSE: 'residential',
      cte.MULTI_FAMILY_HOUSE: 'residential',
      cte.ROW_HOUSE: 'residential',
      cte.MID_RISE_APARTMENT: 'residential',
      cte.HIGH_RISE_APARTMENT: 'residential',
      cte.OFFICE_AND_ADMINISTRATION: 'non-residential',
      cte.SMALL_OFFICE: 'non-residential',
      cte.MEDIUM_OFFICE: 'non-residential',
      cte.LARGE_OFFICE: 'non-residential',
      cte.COURTHOUSE: 'non-residential',
      cte.FIRE_STATION: 'non-residential',
      cte.PENITENTIARY: 'non-residential',
      cte.POLICE_STATION: 'non-residential',
      cte.POST_OFFICE: 'non-residential',
      cte.LIBRARY: 'non-residential',
      cte.EDUCATION: 'non-residential',
      cte.PRIMARY_SCHOOL: 'non-residential',
      cte.PRIMARY_SCHOOL_WITH_SHOWER: 'non-residential',
      cte.SECONDARY_SCHOOL: 'non-residential',
      cte.UNIVERSITY: 'non-residential',
      cte.LABORATORY_AND_RESEARCH_CENTER: 'non-residential',
      cte.STAND_ALONE_RETAIL: 'non-residential',
      cte.HOSPITAL: 'non-residential',
      cte.OUT_PATIENT_HEALTH_CARE: 'non-residential',
      cte.HEALTH_CARE: 'non-residential',
      cte.RETIREMENT_HOME_OR_ORPHANAGE: 'non-residential',
      cte.COMMERCIAL: 'non-residential',
      cte.STRIP_MALL: 'non-residential',
      cte.SUPERMARKET: 'non-residential',
      cte.RETAIL_SHOP_WITHOUT_REFRIGERATED_FOOD: 'non-residential',
      cte.RETAIL_SHOP_WITH_REFRIGERATED_FOOD: 'non-residential',
      cte.RESTAURANT: 'non-residential',
      cte.QUICK_SERVICE_RESTAURANT: 'non-residential',
      cte.FULL_SERVICE_RESTAURANT: 'non-residential',
      cte.HOTEL: 'non-residential',
      cte.HOTEL_MEDIUM_CLASS: 'non-residential',
      cte.SMALL_HOTEL: 'non-residential',
      cte.LARGE_HOTEL: 'non-residential',
      cte.DORMITORY: 'non-residential',
      cte.EVENT_LOCATION: 'non-residential',
      cte.CONVENTION_CENTER: 'non-residential',
      cte.HALL: 'non-residential',
      cte.GREEN_HOUSE: 'non-residential',
      cte.INDUSTRY: 'non-residential',
      cte.WORKSHOP: 'non-residential',
      cte.WAREHOUSE: 'non-residential',
      cte.WAREHOUSE_REFRIGERATED: 'non-residential',
      cte.SPORTS_LOCATION: 'non-residential',
      cte.SPORTS_ARENA: 'non-residential',
      cte.GYMNASIUM: 'non-residential',
      cte.MOTION_PICTURE_THEATRE: 'non-residential',
      cte.MUSEUM: 'non-residential',
      cte.PERFORMING_ARTS_THEATRE: 'non-residential',
      cte.TRANSPORTATION: 'non-residential',
      cte.AUTOMOTIVE_FACILITY: 'non-residential',
      cte.PARKING_GARAGE: 'non-residential',
      cte.RELIGIOUS: 'non-residential',
      cte.NON_HEATED: 'non-residential',
      cte.DATACENTER: 'n/a',
      cte.FARM: 'n/a'
    }

  @property
  def dictionary(self) -> dict:
    """
    Get the dictionary
    :return: {}
    """
    return self._dictionary
