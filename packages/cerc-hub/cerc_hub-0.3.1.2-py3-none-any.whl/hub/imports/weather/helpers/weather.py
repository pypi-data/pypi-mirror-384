"""
weather helper
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2022 Concordia CERC group
Project Coder Pilar Monsalvete Alvarez de Uribarri pilar.monsalvete@concordia.ca
"""

import logging
import math
import hub.helpers.constants as cte
from datetime import datetime, timedelta

class Weather:
  """
  Weather class
  """

  _epw_file = {
    'CA.02.5935': 'https://energyplus-weather.s3.amazonaws.com/north_and_central_america_wmo_region_4/CAN/BC/CAN_BC_Summerland.717680_CWEC/CAN_BC_Summerland.717680_CWEC.epw',
    'CA.10.06': 'https://energyplus-weather.s3.amazonaws.com/north_and_central_america_wmo_region_4/CAN/PQ/CAN_PQ_Montreal.Intl.AP.716270_CWEC/CAN_PQ_Montreal.Intl.AP.716270_CWEC.epw',
    'CA.10.13': 'https://energyplus-weather.s3.amazonaws.com/north_and_central_america_wmo_region_4/CAN/PQ/CAN_PQ_Montreal.Intl.AP.716270_CWEC/CAN_PQ_Montreal.Intl.AP.716270_CWEC.epw',
    'CA.10.14': 'https://energyplus-weather.s3.amazonaws.com/north_and_central_america_wmo_region_4/CAN/PQ/CAN_PQ_Montreal.Intl.AP.716270_CWEC/CAN_PQ_Montreal.Intl.AP.716270_CWEC.epw',
    'CA.10.16': 'https://energyplus-weather.s3.amazonaws.com/north_and_central_america_wmo_region_4/CAN/PQ/CAN_PQ_Montreal.Intl.AP.716270_CWEC/CAN_PQ_Montreal.Intl.AP.716270_CWEC.epw',
    'DE.01.082': 'https://energyplus-weather.s3.amazonaws.com/europe_wmo_region_6/DEU/DEU_Stuttgart.107380_IWEC/DEU_Stuttgart.107380_IWEC.epw',
    'US.NY.047': 'https://energyplus-weather.s3.amazonaws.com/north_and_central_america_wmo_region_4/USA/NY/USA_NY_New.York.City-Central.Park.94728_TMY/USA_NY_New.York.City-Central.Park.94728_TMY.epw',
    'CA.10.12': 'https://energyplus-weather.s3.amazonaws.com/north_and_central_america_wmo_region_4/CAN/PQ/CAN_PQ_Quebec.717140_CWEC/CAN_PQ_Quebec.717140_CWEC.epw',
    'CA.10.03': 'https://energyplus-weather.s3.amazonaws.com/north_and_central_america_wmo_region_4/CAN/PQ/CAN_PQ_Quebec.717140_CWEC/CAN_PQ_Quebec.717140_CWEC.epw',
    'IL.01.': 'https://energyplus-weather.s3.amazonaws.com/europe_wmo_region_6/ISR/ISR_Eilat.401990_MSI/ISR_Eilat.401990_MSI.epw',
    'ES.07.PM': 'https://energyplus-weather.s3.amazonaws.com/europe_wmo_region_6/ESP/ESP_Palma.083060_SWEC/ESP_Palma.083060_SWEC.epw'
  }
  # todo: this dictionary need to be completed, a data science student task?

  @staticmethod
  def sky_temperature(ambient_temperature):
    """
    Get sky temperature from ambient temperature in Celsius
    :return: List[float]
    """
    # Swinbank - Source sky model approximation(1963) based on cloudiness statistics(32 %) in the United States
    # ambient temperatures( in °C)
    # sky temperatures( in °C)
    values = []
    for temperature in ambient_temperature:
      value = 0.037536 * math.pow((temperature + cte.KELVIN), 1.5) \
              + 0.32 * (temperature + cte.KELVIN) - cte.KELVIN
      values.append(value)
    return values

  @staticmethod
  def cold_water_temperature(ambient_temperature):
    """
    Get cold water temperature from ambient temperature in Celsius
    :return: dict
    """
    # Equation from "TOWARDS DEVELOPMENT OF AN ALGORITHM FOR MAINS WATER TEMPERATURE", 2004, Jay Burch
    # and Craig Christensen, National Renewable Energy Laboratory
    # ambient temperatures( in °C)
    # cold water temperatures( in °C)
    t_out_fahrenheit = [1.8 * t_out + 32 for t_out in ambient_temperature]
    t_out_average = sum(t_out_fahrenheit) / len(t_out_fahrenheit)
    max_difference = max(t_out_fahrenheit) - min(t_out_fahrenheit)
    factor_ratio = 0.8
    ratio = 0.4 + 0.01 * (t_out_average - 44)
    lag = 35 - (t_out_average - 35)
    number_of_day = [a for a in range(1, 366)]
    day_of_year = [day for day in number_of_day for _ in range(24)]
    cold_temperature_fahrenheit = []
    cold_temperature = []
    for i in range(len(ambient_temperature)):
      cold_temperature_fahrenheit.append(t_out_average + 8 + ratio * factor_ratio * (max_difference / 2) *
                                         math.sin(math.radians(0.986 * (day_of_year[i] - 15 - lag) - 90)))
      cold_temperature.append((cold_temperature_fahrenheit[i] - 32) / 1.8)
    return cold_temperature

  def epw_file(self, region_code):
    """
    returns the url for the weather file for the given location or default (Montreal data)
    :return: str
    """
    if region_code not in self._epw_file:
      logging.warning('Specific weather data unknown for %s using Montreal data instead', region_code)
      return self._epw_file['CA.10.06']
    return self._epw_file[region_code]
