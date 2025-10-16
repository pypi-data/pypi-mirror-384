"""
Co2AnalysisFactory retrieves the specific CO2 analysis module for the given region
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2019 - 2025 Concordia CERC group
Project Coder Koa Wells kekoa.wells@concordia.ca
"""

from hub.helpers.utils import validate_import_export_type
from hub.imports.co2_analysis.ecoinvent_co2_analysis_parameters import EcoinventCo2AnalysisParameters


class Co2AnalysisFactory:
  """
  Co2AnalysisFactory class
  """
  def __init__(self, handler: str, city):
    self._handler = '_' + handler.lower()
    validate_import_export_type(Co2AnalysisFactory, handler)
    self._city = city

  def _ecoinvent(self):
    """
    Enrich the city by using NREL information
    """
    EcoinventCo2AnalysisParameters(self._city).enrich_buildings()

  def enrich(self):
    """
    Enrich the city given to the class using the class given handler
    :return: None
    """
    _handlers = {
      '_ecoinvent': self._ecoinvent,
    }
    for building in self._city.buildings:
      _ = building.thermal_zones_from_internal_zones  # ensure internal zones initialization
    _handlers[self._handler]()
    return
