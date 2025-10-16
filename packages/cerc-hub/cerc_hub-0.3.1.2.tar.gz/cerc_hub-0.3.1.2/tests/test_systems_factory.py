"""
TestSystemsFactory
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2023 Concordia CERC group
Project Coder Pilar Monsalvete Alvarez de Uribarri pilar.monsalvete@concordia.ca
"""

import subprocess
from pathlib import Path
from unittest import TestCase
import copy
from typing import cast

import hub.helpers.constants as cte
from hub.exports.energy_building_exports_factory import EnergyBuildingsExportsFactory
from hub.exports.exports_factory import ExportsFactory
from hub.helpers.dictionaries import Dictionaries
from hub.imports.construction_factory import ConstructionFactory
from hub.imports.geometry_factory import GeometryFactory
from hub.imports.weather_factory import WeatherFactory
from hub.imports.results_factory import ResultFactory
from hub.imports.usage_factory import UsageFactory
from hub.imports.energy_systems_factory import EnergySystemsFactory
from hub.city_model_structure.energy_systems.energy_system import EnergySystem
from hub.city_model_structure.energy_systems.generation_system import GenerationSystem
from hub.city_model_structure.energy_systems.distribution_system import DistributionSystem
from hub.city_model_structure.energy_systems.emission_system import EmissionSystem
from hub.city_model_structure.energy_systems.thermal_storage_system import ThermalStorageSystem
from hub.city_model_structure.energy_systems.non_pv_generation_system import NonPvGenerationSystem


class TestSystemsFactory(TestCase):
  """
  TestSystemsFactory TestCase
  """
  def setUp(self) -> None:
    """
    Test setup
    :return: None
    """
    self._example_path = (Path(__file__).parent / 'tests_data').resolve()
    self._output_path = (Path(__file__).parent / 'tests_outputs').resolve()
    file = 'test.geojson'
    file_path = (self._example_path / file).resolve()
    self._city = GeometryFactory('geojson',
                                 path=file_path,
                                 height_field='citygml_me',
                                 year_of_construction_field='ANNEE_CONS',
                                 function_field='CODE_UTILI',
                                 function_to_hub=Dictionaries().montreal_function_to_hub_function).city

  def test_montreal_custom_system_factory(self):
    """
    Enrich the city with the construction information and verify it
    """
    for building in self._city.buildings:
      building.energy_systems_archetype_name = 'system 1 gas'

    EnergySystemsFactory('montreal_custom', self._city).enrich()
    self.assertEqual(1, len(self._city.generic_energy_systems))

  def test_montreal_custom_system_results(self):
    """
    Enrich the city with the construction information and verify it
    """
    ConstructionFactory('nrcan', self._city).enrich()
    UsageFactory('nrcan', self._city).enrich()
    WeatherFactory('epw', self._city).enrich()
    ExportsFactory('sra', self._city, self._output_path).export()
    sra_path = (self._output_path / f'{self._city.name}_sra.xml').resolve()
    subprocess.run(['sra', str(sra_path)])
    ResultFactory('sra', self._city, self._output_path).enrich()
    EnergyBuildingsExportsFactory('insel_monthly_energy_balance', self._city, self._output_path).export()
    for building in self._city.buildings:
      insel_path = (self._output_path / f'{building.name}.insel')
      subprocess.run(['insel', str(insel_path)])
    ResultFactory('insel_monthly_energy_balance', self._city, self._output_path).enrich()

    for building in self._city.buildings:
      building.energy_systems_archetype_name = 'system 1 gas pv'
    EnergySystemsFactory('montreal_custom', self._city).enrich()
    # Need to assign energy systems to buildings:
    for building in self._city.buildings:
      _building_energy_systems = []
      for energy_system in building.energy_systems:
        if cte.HEATING in energy_system.demand_types:
          _generation_system = cast(NonPvGenerationSystem, energy_system.generation_systems[0])
          _generation_system.heat_power = building.heating_peak_load[cte.YEAR][0]
        if cte.COOLING in energy_system.demand_types:
          _generation_system = cast(NonPvGenerationSystem, energy_system.generation_systems[0])
          _generation_system.cooling_power = building.cooling_peak_load[cte.YEAR][0]

    for building in self._city.buildings:
      self.assertLess(0, building.heating_consumption[cte.YEAR][0])
      self.assertLess(0, building.cooling_consumption[cte.YEAR][0])
      self.assertLess(0, building.domestic_hot_water_consumption[cte.YEAR][0])
      self.assertLess(0, building.onsite_electrical_production[cte.YEAR][0])

  def test_montreal_future_system_results(self):
    """
    Enrich the city with the construction information and verify it
    """
    ConstructionFactory('nrcan', self._city).enrich()
    UsageFactory('nrcan', self._city).enrich()
    WeatherFactory('epw', self._city).enrich()
    ExportsFactory('sra', self._city, self._output_path).export()
    sra_path = (self._output_path / f'{self._city.name}_sra.xml').resolve()
    subprocess.run(['sra', str(sra_path)])
    ResultFactory('sra', self._city, self._output_path).enrich()
    EnergyBuildingsExportsFactory('insel_monthly_energy_balance', self._city, self._output_path).export()
    for building in self._city.buildings:
      insel_path = (self._output_path / f'{building.name}.insel')
      subprocess.run(['insel', str(insel_path)])
    ResultFactory('insel_monthly_energy_balance', self._city, self._output_path).enrich()

    for building in self._city.buildings:
      building.energy_systems_archetype_name = ('Central Hydronic Air and Gas Source Heating System with Unitary Split '
                                                'Cooling and Air Source HP DHW and Grid Tied PV')
    EnergySystemsFactory('montreal_future', self._city).enrich()
    # Need to assign energy systems to buildings:
    for building in self._city.buildings:
      _building_energy_systems = []
      for energy_system in building.energy_systems:
        if cte.HEATING in energy_system.demand_types:
          _generation_system = cast(NonPvGenerationSystem, energy_system.generation_systems[0])
          _generation_system.nominal_heat_output = building.heating_peak_load[cte.YEAR][0]
        if cte.COOLING in energy_system.demand_types:
          _generation_system = cast(NonPvGenerationSystem, energy_system.generation_systems[0])
          _generation_system.nominal_cooling_output = building.cooling_peak_load[cte.YEAR][0]

    for building in self._city.buildings:
      self.assertLess(0, building.heating_consumption[cte.YEAR][0])
      self.assertLess(0, building.cooling_consumption[cte.YEAR][0])
      self.assertLess(0, building.domestic_hot_water_consumption[cte.YEAR][0])
      if 'PV' in building.energy_systems_archetype_name:
        self.assertLess(0, building.onsite_electrical_production[cte.YEAR][0])

  def test_palma_system_results(self):
    """
    Enrich the city with the construction information and verify it
    """
    ConstructionFactory('nrcan', self._city).enrich()
    UsageFactory('nrcan', self._city).enrich()
    WeatherFactory('epw', self._city).enrich()
    ExportsFactory('sra', self._city, self._output_path).export()
    sra_path = (self._output_path / f'{self._city.name}_sra.xml').resolve()
    subprocess.run(['sra', str(sra_path)])
    ResultFactory('sra', self._city, self._output_path).enrich()
    EnergyBuildingsExportsFactory('insel_monthly_energy_balance', self._city, self._output_path).export()
    for building in self._city.buildings:
      insel_path = (self._output_path / f'{building.name}.insel')
      subprocess.run(['insel', str(insel_path)])
    ResultFactory('insel_monthly_energy_balance', self._city, self._output_path).enrich()

    for building in self._city.buildings:
      building.energy_systems_archetype_name = 'PV and heat pump'
    EnergySystemsFactory('palma', self._city).enrich()
    # Need to assign energy systems to buildings:
    for building in self._city.buildings:
      _building_energy_systems = []
      for energy_system in building.energy_systems:
        if cte.HEATING in energy_system.demand_types:
          _generation_system = cast(NonPvGenerationSystem, energy_system.generation_systems[0])
          _generation_system.nominal_heat_output = building.heating_peak_load[cte.YEAR][0]
        if cte.COOLING in energy_system.demand_types:
          _generation_system = cast(NonPvGenerationSystem, energy_system.generation_systems[0])
          _generation_system.nominal_cooling_output = building.cooling_peak_load[cte.YEAR][0]

    for building in self._city.buildings:
      self.assertLess(0, building.heating_consumption[cte.YEAR][0])
      self.assertLess(0, building.cooling_consumption[cte.YEAR][0])
      self.assertLess(0, building.domestic_hot_water_consumption[cte.YEAR][0])
      self.assertLess(0, building.onsite_electrical_production[cte.YEAR][0])