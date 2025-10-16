"""
Dictionaries module for hub usage to NRCAN usage
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2022 Concordia CERC group
Project Coder Guille Gutierrez Guillermo.GutierrezMorote@concordia.ca
"""

import hub.helpers.constants as cte


class HubUsageToNrcanUsage:
  """
  Hub usage to nrcan usage class
  """

  def __init__(self):
    self._dictionary = {
      cte.RESIDENTIAL: 'Multi-unit residential building',
      cte.SINGLE_FAMILY_HOUSE: 'Multi-unit residential building',
      cte.MULTI_FAMILY_HOUSE: 'Multi-unit residential building',
      cte.ROW_HOUSE: 'Multi-unit residential building',
      cte.MID_RISE_APARTMENT: 'Multi-unit residential building',
      cte.HIGH_RISE_APARTMENT: 'Multi-unit residential building',
      cte.OFFICE_AND_ADMINISTRATION: 'Office',
      cte.SMALL_OFFICE: 'Office',
      cte.MEDIUM_OFFICE: 'Office',
      cte.LARGE_OFFICE: 'Office',
      cte.COURTHOUSE: 'Courthouse',
      cte.FIRE_STATION: 'Fire station',
      cte.PENITENTIARY: 'Penitentiary',
      cte.POLICE_STATION: 'Police station',
      cte.POST_OFFICE: 'Post office',
      cte.LIBRARY: 'Library',
      cte.EDUCATION: 'School/university',
      cte.PRIMARY_SCHOOL: 'School/university',
      cte.PRIMARY_SCHOOL_WITH_SHOWER: 'School/university',
      cte.SECONDARY_SCHOOL: 'School/university',
      cte.UNIVERSITY: 'School/university',
      cte.LABORATORY_AND_RESEARCH_CENTER: 'School/university',
      cte.STAND_ALONE_RETAIL: 'Retail area',
      cte.HOSPITAL: 'Hospital',
      cte.OUT_PATIENT_HEALTH_CARE: 'Health care clinic',
      cte.HEALTH_CARE: 'Health care clinic',
      cte.RETIREMENT_HOME_OR_ORPHANAGE: 'Health care clinic',
      cte.COMMERCIAL: 'Retail area',
      cte.STRIP_MALL: 'Retail area',
      cte.SUPERMARKET: 'Retail area',
      cte.RETAIL_SHOP_WITHOUT_REFRIGERATED_FOOD: 'Retail area',
      cte.RETAIL_SHOP_WITH_REFRIGERATED_FOOD: 'Retail area',
      cte.RESTAURANT: 'Dining - bar lounge/leisure',
      cte.QUICK_SERVICE_RESTAURANT: 'Dining - cafeteria/fast food',
      cte.FULL_SERVICE_RESTAURANT: 'Dining - bar lounge/leisure',
      cte.HOTEL: 'Hotel/Motel',
      cte.HOTEL_MEDIUM_CLASS: 'Hotel/Motel',
      cte.SMALL_HOTEL: 'Hotel/Motel',
      cte.LARGE_HOTEL: 'Hotel/Motel',
      cte.DORMITORY: 'Dormitory',
      cte.EVENT_LOCATION: 'Convention centre',
      cte.CONVENTION_CENTER: 'Convention centre',
      cte.HALL: 'Town hall',
      cte.GREEN_HOUSE: 'n/a',
      cte.INDUSTRY: 'Manufacturing facility',
      cte.WORKSHOP: 'Workshop',
      cte.WAREHOUSE: 'Warehouse',
      cte.WAREHOUSE_REFRIGERATED: 'Warehouse',
      cte.SPORTS_LOCATION: 'Exercise centre',
      cte.SPORTS_ARENA: 'Sports arena',
      cte.GYMNASIUM: 'Gymnasium',
      cte.MOTION_PICTURE_THEATRE: 'Motion picture theatre',
      cte.MUSEUM: 'Museum',
      cte.PERFORMING_ARTS_THEATRE: 'Performing arts theatre',
      cte.TRANSPORTATION: 'Transportation facility',
      cte.AUTOMOTIVE_FACILITY: 'Automotive facility',
      cte.PARKING_GARAGE: 'Storage garage',
      cte.RELIGIOUS: 'Religious building',
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
