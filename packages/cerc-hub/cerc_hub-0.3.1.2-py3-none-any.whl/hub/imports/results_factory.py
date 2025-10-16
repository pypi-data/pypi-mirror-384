"""
Result factory retrieve the specific tool results and store the data in the given city
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2022 Concordia CERC group
Project Coder Guille Gutierrez guillermo.gutierrezmorote@concordia.ca
Code contributors: Pilar Monsalvete Alvarez de Uribarri pilar.monsalvete@concordia.ca
"""
from pathlib import Path

from hub.helpers.utils import validate_import_export_type
from hub.imports.results.energy_plus import EnergyPlus
from hub.imports.results.insel_monthly_energry_balance import InselMonthlyEnergyBalance
from hub.imports.results.simplified_radiosity_algorithm import SimplifiedRadiosityAlgorithm

from hub.imports.results.ep_multiple_buildings import EnergyPlusMultipleBuildings
from hub.imports.results.energy_plus_single_building import EnergyPlusSingleBuilding


class ResultFactory:
  """
  ResultFactory class
  """

  def __init__(self, handler, city, base_path=None, hp_model=None):
    """

    :param handler: pointer to results class to be called
    :param city: the city object
    :param base_path: the path to result output file
    :param hp_model: (optional) the heat pump model for which
    results are being retrieved
    """
    if base_path is None:
      base_path = Path(Path(__file__).parent.parent / 'data/results')
    self._handler = '_' + handler.lower().replace(' ', '_')
    validate_import_export_type(ResultFactory, handler)
    self._city = city
    self._base_path = Path(base_path)
    self._hp_model = hp_model

  def _sra(self):
    """
    Enrich the city with Simplified Radiosity Algorithm results
    """
    SimplifiedRadiosityAlgorithm(self._city, self._base_path).enrich()

  def _insel_monthly_energy_balance(self):
    """
    Enrich the city with insel monthly energy balance results
    """
    InselMonthlyEnergyBalance(self._city, self._base_path).enrich()

  def _energy_plus_single_building(self):
    """
    Enrich the city with energy plus results
    """
    EnergyPlusSingleBuilding(self._city, self._base_path).enrich()

  def _energy_plus_multiple_buildings(self):
    """
    Enrich the city with energy plus results
    """
    EnergyPlusMultipleBuildings(self._city, self._base_path).enrich()

  def _cerc_idf(self):
    EnergyPlus(self._city, self._base_path).enrich()

  def enrich(self):
    """
    Enrich the city given to the class using the usage factory given handler
    :return: None
    """
    _handlers = {
      '_sra': self._sra,
      '_insel_monthly_energy_balance': self._insel_monthly_energy_balance,
      '_energy_plus_single_building': self._energy_plus_single_building,
      '_energy_plus_multiple_buildings': self._energy_plus_multiple_buildings,
      '_cerc_idf': self._cerc_idf,
    }
    return _handlers[self._handler]()
