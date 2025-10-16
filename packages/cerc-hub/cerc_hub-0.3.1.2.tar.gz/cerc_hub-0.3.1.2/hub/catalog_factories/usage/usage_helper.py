"""
Usage helper
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2022 Concordia CERC group
Project Coder Pilar Monsalvete Alvarez de Uribarri pilar.monsalvete@concordia.ca
"""
from typing import Dict

import hub.helpers.constants as cte


class UsageHelper:
  """
  Usage helper class
  """
  _nrcan_schedule_type_to_hub_schedule_type = {
    'Lighting': cte.LIGHTING,
    'Occupancy': cte.OCCUPANCY,
    'Equipment': cte.APPLIANCES,
    'Thermostat Setpoint Cooling': cte.COOLING_SET_POINT,
    'Thermostat Setpoint Heating': cte.HEATING_SET_POINT,
    'Fan': cte.HVAC_AVAILABILITY,
    'Service Water Heating': cte.DOMESTIC_HOT_WATER
  }
  _nrcan_data_type_to_hub_data_type = {
    'FRACTION': cte.FRACTION,
    'ON_OFF': cte.ON_OFF,
    'TEMPERATURE': cte.ANY_NUMBER
  }

  _nrcan_time_to_hub_time = {
    'Hourly': cte.HOUR,
    'Constant': cte.CONSTANT
  }

  _nrcan_day_type_to_hub_days = {
    'Default|Wkdy': [cte.MONDAY, cte.TUESDAY, cte.WEDNESDAY, cte.THURSDAY, cte.FRIDAY],
    'Sun|Hol': [cte.SUNDAY, cte.HOLIDAY],
    'Sat': [cte.SATURDAY],
    'Default|WntrDsn|SmrDsn': [cte.MONDAY,
                               cte.TUESDAY,
                               cte.WEDNESDAY,
                               cte.THURSDAY,
                               cte.FRIDAY,
                               cte.SATURDAY,
                               cte.SUNDAY,
                               cte.HOLIDAY,
                               cte.WINTER_DESIGN_DAY,
                               cte.SUMMER_DESIGN_DAY],
    'Default': [cte.MONDAY,
                cte.TUESDAY,
                cte.WEDNESDAY,
                cte.THURSDAY,
                cte.FRIDAY,
                cte.SATURDAY,
                cte.SUNDAY,
                cte.HOLIDAY,
                cte.WINTER_DESIGN_DAY,
                cte.SUMMER_DESIGN_DAY]

  }

  _comnet_days = [cte.MONDAY,
                  cte.TUESDAY,
                  cte.WEDNESDAY,
                  cte.THURSDAY,
                  cte.FRIDAY,
                  cte.SATURDAY,
                  cte.SUNDAY,
                  cte.HOLIDAY]

  _comnet_data_type_to_hub_data_type = {
    'Fraction': cte.FRACTION,
    'OnOff': cte.ON_OFF,
    'Temperature': cte.ANY_NUMBER
  }

  _comnet_schedules_key_to_comnet_schedules = {
    'C-1 Assembly': 'C-1 Assembly',
    'C-2 Public': 'C-2 Health',
    'C-3 Hotel Motel': 'C-3 Hotel',
    'C-4 Manufacturing': 'C-4 Manufacturing',
    'C-5 Office': 'C-5 Office',
    'C-7 Restaurant': 'C-7 Restaurant',
    'C-8 Retail': 'C-8 Retail',
    'C-9 Schools': 'C-9 School',
    'C-10 Warehouse': 'C-10 Warehouse',
    'C-11 Laboratory': 'C-11 Lab',
    'C-12 Residential': 'C-12 Residential',
    'C-14 Gymnasium': 'C-14 Gymnasium'
  }

  _eilat_schedules_key_to_eilat_schedules = {
    'C-12 Residential': 'C-12 Residential',
    'C-15 Dormitory': 'C-15 Dormitory',
    'C-16 Hotel employees': 'C-16 Hotel employees'
  }

  @property
  def nrcan_day_type_to_hub_days(self):
    """
    Get a dictionary to convert nrcan day types to hub day types
    """
    return self._nrcan_day_type_to_hub_days

  @property
  def nrcan_schedule_type_to_hub_schedule_type(self):
    """
    Get a dictionary to convert nrcan schedule types to hub schedule types
    """
    return self._nrcan_schedule_type_to_hub_schedule_type

  @property
  def nrcan_data_type_to_hub_data_type(self):
    """
    Get a dictionary to convert nrcan data types to hub data types
    """
    return self._nrcan_data_type_to_hub_data_type

  @property
  def nrcan_time_to_hub_time(self):
    """
    Get a dictionary to convert nrcan time to hub time
    """
    return self._nrcan_time_to_hub_time

  @property
  def comnet_data_type_to_hub_data_type(self) -> Dict:
    """
    Get a dictionary to convert comnet data types to hub data types
    """
    return self._comnet_data_type_to_hub_data_type

  @property
  def comnet_schedules_key_to_comnet_schedules(self) -> Dict:
    """
    Get a dictionary to convert hub schedules to comnet schedules
    """
    return self._comnet_schedules_key_to_comnet_schedules

  @property
  def comnet_days(self) -> [str]:
    """
    Get the list of days used in comnet
    """
    return self._comnet_days

  @property
  def eilat_schedules_key_to_eilat_schedules(self) -> [str]:
    """
    Get a dictionary to convert hub schedules to eilat schedules
    """
    return self._eilat_schedules_key_to_eilat_schedules
