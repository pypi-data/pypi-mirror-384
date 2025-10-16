"""
Dictionaries module for hub usage to Comnet usage
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2022 Concordia CERC group
Project Coder Guille Gutierrez Guillermo.GutierrezMorote@concordia.ca
"""

import hub.helpers.constants as cte


class HubUsageToComnetUsage:
  """
  Hub usage to comnet usage class
  """

  def __init__(self):
    self._dictionary = {
      cte.RESIDENTIAL: 'BA Multifamily',
      cte.SINGLE_FAMILY_HOUSE: 'BA Multifamily',
      cte.MULTI_FAMILY_HOUSE: 'BA Multifamily',
      cte.ROW_HOUSE: 'BA Multifamily',
      cte.MID_RISE_APARTMENT: 'BA Multifamily',
      cte.HIGH_RISE_APARTMENT: 'BA Multifamily',
      cte.OFFICE_AND_ADMINISTRATION: 'BA Office',
      cte.SMALL_OFFICE: 'BA Office',
      cte.MEDIUM_OFFICE: 'BA Office',
      cte.LARGE_OFFICE: 'BA Office',
      cte.COURTHOUSE: 'BA Courthouse',
      cte.FIRE_STATION: 'BA Fire Station',
      cte.PENITENTIARY: 'BA Penitentiary',
      cte.POLICE_STATION: 'BA Police Station',
      cte.POST_OFFICE: 'BA Post Office',
      cte.LIBRARY: 'BA Library',
      cte.EDUCATION: 'BA School/University',
      cte.PRIMARY_SCHOOL: 'BA School/University',
      cte.PRIMARY_SCHOOL_WITH_SHOWER: 'BA School/University',
      cte.SECONDARY_SCHOOL: 'BA School/University',
      cte.UNIVERSITY: 'BA School/University',
      cte.LABORATORY_AND_RESEARCH_CENTER: 'BA School/University',
      cte.STAND_ALONE_RETAIL: 'BA Retail',
      cte.HOSPITAL: 'BA Hospital',
      cte.OUT_PATIENT_HEALTH_CARE: 'BA Healthcare Clinic',
      cte.HEALTH_CARE: 'BA Healthcare Clinic',
      cte.RETIREMENT_HOME_OR_ORPHANAGE: 'BA Healthcare Clinic',
      cte.COMMERCIAL: 'BA Retail',
      cte.STRIP_MALL: 'BA Retail',
      cte.SUPERMARKET: 'BA Retail',
      cte.RETAIL_SHOP_WITHOUT_REFRIGERATED_FOOD: 'BA Retail',
      cte.RETAIL_SHOP_WITH_REFRIGERATED_FOOD: 'BA Retail',
      cte.RESTAURANT: 'BA Dining: Bar Lounge/Leisure',
      cte.QUICK_SERVICE_RESTAURANT: 'BA Dining: Cafeteria/Fast Food',
      cte.FULL_SERVICE_RESTAURANT: 'BA Dining: Bar Lounge/Leisure',
      cte.HOTEL: 'BA Hotel',
      cte.HOTEL_MEDIUM_CLASS: 'BA Motel',
      cte.SMALL_HOTEL: 'BA Motel',
      cte.LARGE_HOTEL: 'BA Hotel',
      cte.DORMITORY: 'BA Dormitory',
      cte.EVENT_LOCATION: 'BA Convention Center',
      cte.CONVENTION_CENTER: 'BA Convention Center',
      cte.HALL: 'BA Town Hall',
      cte.GREEN_HOUSE: 'n/a',
      cte.INDUSTRY: 'BA Manufacturing Facility',
      cte.WORKSHOP: 'BA Workshop',
      cte.WAREHOUSE: 'BA Warehouse',
      cte.WAREHOUSE_REFRIGERATED: 'BA Warehouse',
      cte.SPORTS_LOCATION: 'BA Exercise Center',
      cte.SPORTS_ARENA: 'BA Sports Arena',
      cte.GYMNASIUM: 'BA Gymnasium',
      cte.MOTION_PICTURE_THEATRE: 'BA Motion Picture Theater',
      cte.MUSEUM: 'BA Museum',
      cte.PERFORMING_ARTS_THEATRE: 'BA Performing Arts Theater',
      cte.TRANSPORTATION: 'BA Transportation',
      cte.AUTOMOTIVE_FACILITY: 'BA Automotive Facility',
      cte.PARKING_GARAGE: 'BA Parking Garage',
      cte.RELIGIOUS: 'BA Religious Building',
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
