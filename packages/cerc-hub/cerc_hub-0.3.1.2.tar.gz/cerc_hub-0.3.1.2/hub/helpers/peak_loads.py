"""
Cooling and Heating peak loads module
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2023 Concordia CERC group
Project Coder Pilar Monsalvete Alvarez de Uribarri pilar.monsalvete@concordia.ca
Code contributors: Guille Gutierrez guillermo.gutierrezmorote@concordia.ca
"""

import math

import hub.helpers.constants as cte
from hub.helpers.peak_calculation.loads_calculation import LoadsCalculation

_MONTH_STARTING_HOUR = [0, 744, 1416, 2160, 2880, 3624, 4344, 5088, 5832, 6552, 7296, 8016, math.inf]


class PeakLoads:
  """
  PeakLoads class
  """
  def __init__(self, building=None):
    self._building = building

  def _can_be_calculated(self):
    levels_of_detail = self._building.level_of_detail
    can_be_calculated = True
    if levels_of_detail.geometry is None:
      can_be_calculated = False
    elif levels_of_detail.geometry < 1:
      can_be_calculated = False
    if levels_of_detail.construction is None:
      can_be_calculated = False
    elif levels_of_detail.construction < 1:
      can_be_calculated = False
    if levels_of_detail.usage is None:
      can_be_calculated = False
    elif levels_of_detail.usage < 1:
      can_be_calculated = False
    if levels_of_detail.weather is None:
      can_be_calculated = False
    elif levels_of_detail.weather < 2:
      can_be_calculated = False
    if levels_of_detail.surface_radiation is None:
      can_be_calculated = False
    elif levels_of_detail.surface_radiation < 2:
      can_be_calculated = False
    return can_be_calculated

  @staticmethod
  def peak_loads_from_hourly(hourly_values):
    """
    Get peak loads from hourly
    :return: [int]
    """
    month = 1
    peaks = [0 for _ in range(12)]
    for i in range(0, len(hourly_values)):
      if _MONTH_STARTING_HOUR[month] <= i:
        month += 1
      if hourly_values[i] > peaks[month-1]:
        peaks[month-1] = hourly_values[i]
    return peaks

  @property
  def heating_peak_loads_from_methodology(self):
    """
    Get heating peak loads by calculate
    :return: [int]
    """
    if not self._can_be_calculated():
      return None
    monthly_heating_loads = []
    ambient_temperature = self._building.external_temperature[cte.HOUR]
    for month in range(0, 12):
      ground_temperature = self._building.ground_temperature[cte.MONTH]['2'][month]
      start_hour = _MONTH_STARTING_HOUR[month]
      end_hour = 8760
      if month < 11:
        end_hour = _MONTH_STARTING_HOUR[month + 1]
      heating_ambient_temperature = min(ambient_temperature[start_hour:end_hour])
      loads = LoadsCalculation(self._building)
      heating_load_transmitted = loads.get_heating_transmitted_load(heating_ambient_temperature, ground_temperature)
      heating_load_ventilation_sensible = loads.get_heating_ventilation_load_sensible(heating_ambient_temperature)
      # todo: include heating ventilation latent
      heating_load_ventilation_latent = 0
      heating_load = heating_load_transmitted + heating_load_ventilation_sensible + heating_load_ventilation_latent
      heating_load = max(heating_load, 0)
      monthly_heating_loads.append(heating_load)
    return monthly_heating_loads

  @property
  def cooling_peak_loads_from_methodology(self):
    """
    Get cooling peak loads by calculate
    :return: [int]
    """
    if not self._can_be_calculated():
      return None
    monthly_cooling_loads = []
    ambient_temperature = self._building.external_temperature[cte.HOUR]
    for month in range(0, 12):
      ground_temperature = self._building.ground_temperature[cte.MONTH]['2'][month]
      cooling_ambient_temperature = -100
      cooling_calculation_hour = -1
      start_hour = _MONTH_STARTING_HOUR[month]
      end_hour = 8760
      if month < 11:
        end_hour = _MONTH_STARTING_HOUR[month + 1]
      for hour in range(start_hour, end_hour):
        temperature = ambient_temperature[hour]
        if temperature > cooling_ambient_temperature:
          cooling_ambient_temperature = temperature
          cooling_calculation_hour = hour
      loads = LoadsCalculation(self._building)
      cooling_load_transmitted = loads.get_cooling_transmitted_load(cooling_ambient_temperature, ground_temperature)
      cooling_load_renovation_sensible = loads.get_cooling_ventilation_load_sensible(cooling_ambient_temperature)
      cooling_load_internal_gains_sensible = loads.get_internal_load_sensible()
      cooling_load_radiation = loads.get_radiation_load(cooling_calculation_hour)
      cooling_load_sensible = cooling_load_transmitted + cooling_load_renovation_sensible - cooling_load_radiation \
                              - cooling_load_internal_gains_sensible

      cooling_load_latent = 0
      cooling_load = cooling_load_sensible + cooling_load_latent
      cooling_load = min(cooling_load, 0)
      monthly_cooling_loads.append(abs(cooling_load))
    return monthly_cooling_loads
