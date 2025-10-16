"""
EnergySystemsFactory retrieve the energy system module for the given region
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2022 Concordia CERC group
Project Coder Pilar Monsalvete pilar.monsalvete@concordi.
Code contributors: Peter Yefi peteryefi@gmail.com
"""
from pathlib import Path

from hub.helpers.utils import validate_import_export_type
from hub.imports.energy_systems.montreal_custom_energy_system_parameters import MontrealCustomEnergySystemParameters
from hub.imports.energy_systems.north_america_custom_energy_system_parameters import \
  NorthAmericaCustomEnergySystemParameters
from hub.imports.energy_systems.montreal_future_energy_systems_parameters import MontrealFutureEnergySystemParameters
from hub.imports.energy_systems.palma_energy_systems_parameters import PalmaEnergySystemParameters


class EnergySystemsFactory:
  """
  EnergySystemsFactory class
  """

  def __init__(self, handler, city, base_path=None):
    if base_path is None:
      base_path = Path(Path(__file__).parent.parent / 'data/energy_systems')
    self._handler = '_' + handler.lower()
    validate_import_export_type(EnergySystemsFactory, handler)
    self._city = city
    self._base_path = base_path

  def _montreal_custom(self):
    """
    Enrich the city by using montreal custom energy systems catalog information
    """
    MontrealCustomEnergySystemParameters(self._city).enrich_buildings()
    self._city.level_of_detail.energy_systems = 1
    for building in self._city.buildings:
      building.level_of_detail.energy_systems = 1

  def _north_america(self):
    """
    Enrich the city by using north america custom energy systems catalog information
    """
    NorthAmericaCustomEnergySystemParameters(self._city).enrich_buildings()
    self._city.level_of_detail.energy_systems = 2
    for building in self._city.buildings:
      building.level_of_detail.energy_systems = 2

  def _montreal_future(self):
    """
    Enrich the city by using north america custom energy systems catalog information
    """
    MontrealFutureEnergySystemParameters(self._city).enrich_buildings()
    self._city.level_of_detail.energy_systems = 2
    for building in self._city.buildings:
      building.level_of_detail.energy_systems = 2

  def _palma(self):
    """
    Enrich the city by using north america custom energy systems catalog information
    """
    PalmaEnergySystemParameters(self._city).enrich_buildings()
    self._city.level_of_detail.energy_systems = 2
    for building in self._city.buildings:
      building.level_of_detail.energy_systems = 2

  def enrich(self):
    """
    Enrich the city given to the class using the class given handler
    :return: None
    """
    _handlers = {
      '_montreal_custom': self._montreal_custom,
      '_north_america': self._north_america,
      '_montreal_future': self._montreal_future,
      '_palma': self._palma,
    }
    return _handlers[self._handler]()
