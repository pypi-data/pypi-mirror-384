"""
WeatherFactory retrieve the specific weather module for the given source format
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2022 Concordia CERC group
Project Coder Pilar Monsalvete Alvarez de Uribarri pilar.monsalvete@concordia.ca
"""

from hub.city_model_structure.city import City
from hub.helpers.utils import validate_import_export_type
from hub.imports.weather.epw_weather_parameters import EpwWeatherParameters


class WeatherFactory:
  """
  WeatherFactory class
  """

  def __init__(self, handler, city: City):
    self._handler = '_' + handler.lower().replace(' ', '_')
    validate_import_export_type(WeatherFactory, handler)
    self._city = city

  def _epw(self):
    """
    Enrich the city with energy plus weather file
    """
    # EnergyPlus Weather
    # to download files: https://energyplus.net/weather
    # description of the format: https://energyplus.net/sites/default/files/pdfs_v8.3.0/AuxiliaryPrograms.pdf
    return EpwWeatherParameters(self._city)

  def enrich(self):
    """
    Enrich the city given to the class using the given weather handler
    :return: None
    """
    _handlers = {
      '_epw': self._epw,
    }
    return _handlers[self._handler]()
