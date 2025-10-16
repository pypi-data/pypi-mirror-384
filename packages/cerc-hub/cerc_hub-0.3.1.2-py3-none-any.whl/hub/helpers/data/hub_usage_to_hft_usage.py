"""
Dictionaries module for hub usage to Hft usage
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2022 Concordia CERC group
Project Coder Guille Gutierrez Guillermo.GutierrezMorote@concordia.ca
"""

import hub.helpers.constants as cte


class HubUsageToHftUsage:
  """
  Hub usage to hft usage class
  """

  def __init__(self):
    self._dictionary = {
      cte.RESIDENTIAL: 'residential',
      cte.SINGLE_FAMILY_HOUSE: 'single family house',
      cte.MULTI_FAMILY_HOUSE: 'multifamily house',
      cte.ROW_HOUSE: 'single family house',
      cte.MID_RISE_APARTMENT: 'multifamily house',
      cte.HIGH_RISE_APARTMENT: 'multifamily house',
      cte.OFFICE_AND_ADMINISTRATION: 'office and administration',
      cte.SMALL_OFFICE: 'office and administration',
      cte.MEDIUM_OFFICE: 'office and administration',
      cte.LARGE_OFFICE: 'office and administration',
      cte.COURTHOUSE: 'office and administration',
      cte.FIRE_STATION: 'office and administration',
      cte.PENITENTIARY: 'school with shower',
      cte.POLICE_STATION: 'office and administration',
      cte.POST_OFFICE: 'office and administration',
      cte.LIBRARY: 'office and administration',
      cte.EDUCATION: 'education',
      cte.PRIMARY_SCHOOL: 'school without shower',
      cte.PRIMARY_SCHOOL_WITH_SHOWER: 'school with shower',
      cte.SECONDARY_SCHOOL: 'education',
      cte.UNIVERSITY: 'education',
      cte.LABORATORY_AND_RESEARCH_CENTER: 'laboratory and research centers',
      cte.STAND_ALONE_RETAIL: 'retail',
      cte.HOSPITAL: 'health care',
      cte.OUT_PATIENT_HEALTH_CARE: 'health care',
      cte.HEALTH_CARE: 'health care',
      cte.RETIREMENT_HOME_OR_ORPHANAGE: 'Home for the aged or orphanage',
      cte.COMMERCIAL: 'retail',
      cte.STRIP_MALL: 'retail',
      cte.SUPERMARKET: 'retail shop / refrigerated food',
      cte.RETAIL_SHOP_WITHOUT_REFRIGERATED_FOOD: 'retail',
      cte.RETAIL_SHOP_WITH_REFRIGERATED_FOOD: 'retail shop / refrigerated food',
      cte.RESTAURANT: 'restaurant',
      cte.QUICK_SERVICE_RESTAURANT: 'restaurant',
      cte.FULL_SERVICE_RESTAURANT: 'restaurant',
      cte.HOTEL: 'hotel',
      cte.HOTEL_MEDIUM_CLASS: 'hotel (Medium-class)',
      cte.SMALL_HOTEL: 'hotel',
      cte.LARGE_HOTEL: 'hotel',
      cte.DORMITORY: 'dormitory',
      cte.EVENT_LOCATION: 'event location',
      cte.CONVENTION_CENTER: 'event location',
      cte.HALL: 'hall',
      cte.GREEN_HOUSE: 'green house',
      cte.INDUSTRY: 'industry',
      cte.WORKSHOP: 'industry',
      cte.WAREHOUSE: 'industry',
      cte.WAREHOUSE_REFRIGERATED: 'industry',
      cte.SPORTS_LOCATION: 'sport location',
      cte.SPORTS_ARENA: 'sport location',
      cte.GYMNASIUM: 'sport location',
      cte.MOTION_PICTURE_THEATRE: 'event location',
      cte.MUSEUM: 'event location',
      cte.PERFORMING_ARTS_THEATRE: 'event location',
      cte.TRANSPORTATION: 'n/a',
      cte.AUTOMOTIVE_FACILITY: 'n/a',
      cte.PARKING_GARAGE: 'n/a',
      cte.RELIGIOUS: 'event location',
      cte.NON_HEATED: 'non-heated',
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
