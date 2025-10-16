"""
Dictionaries module for hub function to NREL construction function
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2022 Concordia CERC group
Project Coder Guille Gutierrez Guillermo.GutierrezMorote@concordia.ca
"""

import hub.helpers.constants as cte


class HubFunctionToNrelConstructionFunction:
  """
  Hub function to nrel construction function
  """

  def __init__(self):
    self._dictionary = {
      cte.RESIDENTIAL: 'residential',
      cte.SINGLE_FAMILY_HOUSE: 'residential',
      cte.MULTI_FAMILY_HOUSE: 'midrise apartment',
      cte.ROW_HOUSE: 'midrise apartment',
      cte.MID_RISE_APARTMENT: 'midrise apartment',
      cte.HIGH_RISE_APARTMENT: 'high-rise apartment',
      cte.OFFICE_AND_ADMINISTRATION: 'medium office',
      cte.SMALL_OFFICE: 'small office',
      cte.MEDIUM_OFFICE: 'medium office',
      cte.LARGE_OFFICE: 'large office',
      cte.COURTHOUSE: 'medium office',
      cte.FIRE_STATION: 'n/a',
      cte.PENITENTIARY: 'large hotel',
      cte.POLICE_STATION: 'n/a',
      cte.POST_OFFICE: 'medium office',
      cte.LIBRARY: 'medium office',
      cte.EDUCATION: 'secondary school',
      cte.PRIMARY_SCHOOL: 'primary school',
      cte.PRIMARY_SCHOOL_WITH_SHOWER: 'primary school',
      cte.SECONDARY_SCHOOL: 'secondary school',
      cte.UNIVERSITY: 'secondary school',
      cte.LABORATORY_AND_RESEARCH_CENTER: 'secondary school',
      cte.STAND_ALONE_RETAIL: 'stand-alone retail',
      cte.HOSPITAL: 'hospital',
      cte.OUT_PATIENT_HEALTH_CARE: 'outpatient healthcare',
      cte.HEALTH_CARE: 'outpatient healthcare',
      cte.RETIREMENT_HOME_OR_ORPHANAGE: 'small hotel',
      cte.COMMERCIAL: 'strip mall',
      cte.STRIP_MALL: 'strip mall',
      cte.SUPERMARKET: 'supermarket',
      cte.RETAIL_SHOP_WITHOUT_REFRIGERATED_FOOD: 'stand-alone retail',
      cte.RETAIL_SHOP_WITH_REFRIGERATED_FOOD: 'stand-alone retail',
      cte.RESTAURANT: 'full service restaurant',
      cte.QUICK_SERVICE_RESTAURANT: 'quick service restaurant',
      cte.FULL_SERVICE_RESTAURANT: 'full service restaurant',
      cte.HOTEL: 'small hotel',
      cte.HOTEL_MEDIUM_CLASS: 'small hotel',
      cte.SMALL_HOTEL: 'small hotel',
      cte.LARGE_HOTEL: 'large hotel',
      cte.DORMITORY: 'small hotel',
      cte.EVENT_LOCATION: 'n/a',
      cte.CONVENTION_CENTER: 'n/a',
      cte.HALL: 'n/a',
      cte.GREEN_HOUSE: 'n/a',
      cte.INDUSTRY: 'n/a',
      cte.WORKSHOP: 'n/a',
      cte.WAREHOUSE: 'warehouse',
      cte.WAREHOUSE_REFRIGERATED: 'warehouse',
      cte.SPORTS_LOCATION: 'n/a',
      cte.SPORTS_ARENA: 'n/a',
      cte.GYMNASIUM: 'n/a',
      cte.MOTION_PICTURE_THEATRE: 'n/a',
      cte.MUSEUM: 'n/a',
      cte.PERFORMING_ARTS_THEATRE: 'n/a',
      cte.TRANSPORTATION: 'n/a',
      cte.AUTOMOTIVE_FACILITY: 'n/a',
      cte.PARKING_GARAGE: 'n/a',
      cte.RELIGIOUS: 'n/a',
      cte.NON_HEATED: 'n/a',
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
