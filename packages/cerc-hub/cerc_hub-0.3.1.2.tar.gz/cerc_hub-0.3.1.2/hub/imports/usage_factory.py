"""
UsageFactory retrieve the specific usage module for the given region
This factory can only be called after calling the construction factory so the thermal zones are created.
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2022 Concordia CERC group
Project Coder Guille Gutierrez guillermo.gutierrezmorote@concordia.ca
Code contributors: Pilar Monsalvete Alvarez de Uribarri pilar.monsalvete@concordia.ca
"""
from hub.helpers.utils import validate_import_export_type
from hub.imports.usage.comnet_usage_parameters import ComnetUsageParameters
from hub.imports.usage.nrcan_usage_parameters import NrcanUsageParameters
from hub.imports.usage.eilat_usage_parameters import EilatUsageParameters
from hub.imports.usage.palma_usage_parameters import PalmaUsageParameters


class UsageFactory:
  """
  UsageFactory class
  """
  def __init__(self, handler, city):
    self._handler = '_' + handler.lower()
    validate_import_export_type(UsageFactory, handler)
    self._city = city

  def _comnet(self):
    """
    Enrich the city with COMNET usage library
    """
    ComnetUsageParameters(self._city).enrich_buildings()
    self._city.level_of_detail.usage = 2
    for building in self._city.buildings:
      building.level_of_detail.usage = 2

  def _nrcan(self):
    """
    Enrich the city with NRCAN usage library
    """
    NrcanUsageParameters(self._city).enrich_buildings()
    self._city.level_of_detail.usage = 2
    for building in self._city.buildings:
      building.level_of_detail.usage = 2

  def _eilat(self):
    """
    Enrich the city with Eilat usage library
    """
    EilatUsageParameters(self._city).enrich_buildings()
    self._city.level_of_detail.usage = 2
    for building in self._city.buildings:
      building.level_of_detail.usage = 2

  def _palma(self):
    """
    Enrich the city with Palma usage library
    """
    PalmaUsageParameters(self._city).enrich_buildings()
    self._city.level_of_detail.usage = 2
    for building in self._city.buildings:
      building.level_of_detail.usage = 2

  def enrich(self):
    """
    Enrich the city given to the class using the usage factory given handler
    :return: None
    """
    _handlers = {
      '_comnet': self._comnet,
      '_nrcan': self._nrcan,
      '_eilat': self._eilat,
      '_palma': self._palma,
    }
    return _handlers[self._handler]()
