"""
Dictionaries module for hub function to nrcan construction function
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2022 Concordia CERC group
Project Coder Guille Gutierrez Guillermo.GutierrezMorote@concordia.ca
"""

import hub.helpers.constants as cte


class HubFunctionToNrcanConstructionFunction:
  """
  Hub function to nrcan construction function class
  """
  def __init__(self):
    self._dictionary = {
      cte.RESIDENTIAL: 'MidriseApartment',
      cte.SINGLE_FAMILY_HOUSE: 'MidriseApartment',
      cte.MULTI_FAMILY_HOUSE: 'HighriseApartment',
      cte.ROW_HOUSE: 'MidriseApartment',
      cte.MID_RISE_APARTMENT: 'MidriseApartment',
      cte.HIGH_RISE_APARTMENT: 'HighriseApartment',
      cte.OFFICE_AND_ADMINISTRATION: 'MediumOffice',
      cte.SMALL_OFFICE: 'SmallOffice',
      cte.MEDIUM_OFFICE: 'MediumOffice',
      cte.LARGE_OFFICE: 'LargeOffice',
      cte.COURTHOUSE: 'MediumOffice',
      cte.FIRE_STATION: 'n/a',
      cte.PENITENTIARY: 'LargeHotel',
      cte.POLICE_STATION: 'n/a',
      cte.POST_OFFICE: 'MediumOffice',
      cte.LIBRARY: 'MediumOffice',
      cte.EDUCATION: 'SecondarySchool',
      cte.PRIMARY_SCHOOL: 'PrimarySchool',
      cte.PRIMARY_SCHOOL_WITH_SHOWER: 'PrimarySchool',
      cte.SECONDARY_SCHOOL: 'SecondarySchool',
      cte.UNIVERSITY: 'SecondarySchool',
      cte.LABORATORY_AND_RESEARCH_CENTER: 'SecondarySchool',
      cte.STAND_ALONE_RETAIL: 'RetailStandalone',
      cte.HOSPITAL: 'Hospital',
      cte.OUT_PATIENT_HEALTH_CARE: 'Outpatient',
      cte.HEALTH_CARE: 'Outpatient',
      cte.RETIREMENT_HOME_OR_ORPHANAGE: 'SmallHotel',
      cte.COMMERCIAL: 'RetailStripmall',
      cte.STRIP_MALL: 'RetailStripmall',
      cte.SUPERMARKET: 'RetailStripmall',
      cte.RETAIL_SHOP_WITHOUT_REFRIGERATED_FOOD: 'RetailStandalone',
      cte.RETAIL_SHOP_WITH_REFRIGERATED_FOOD: 'RetailStandalone',
      cte.RESTAURANT: 'FullServiceRestaurant',
      cte.QUICK_SERVICE_RESTAURANT: 'QuickServiceRestaurant',
      cte.FULL_SERVICE_RESTAURANT: 'FullServiceRestaurant',
      cte.HOTEL: 'SmallHotel',
      cte.HOTEL_MEDIUM_CLASS: 'SmallHotel',
      cte.SMALL_HOTEL: 'SmallHotel',
      cte.LARGE_HOTEL: 'LargeHotel',
      cte.DORMITORY: 'SmallHotel',
      cte.EVENT_LOCATION: 'n/a',
      cte.CONVENTION_CENTER: 'n/a',
      cte.HALL: 'n/a',
      cte.GREEN_HOUSE: 'n/a',
      cte.INDUSTRY: 'n/a',
      cte.WORKSHOP: 'n/a',
      cte.WAREHOUSE: 'Warehouse',
      cte.WAREHOUSE_REFRIGERATED: 'Warehouse',
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
