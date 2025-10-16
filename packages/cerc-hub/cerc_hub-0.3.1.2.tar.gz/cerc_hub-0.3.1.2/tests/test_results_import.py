"""
TestExports test and validate the city export formats
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2022 Concordia CERC group
Project Coder Guille Gutierrez guillermo.gutierrezmorote@concordia.ca
"""

import subprocess
from pathlib import Path
from unittest import TestCase

import hub.helpers.constants as cte
from hub.exports.energy_building_exports_factory import EnergyBuildingsExportsFactory
from hub.exports.exports_factory import ExportsFactory
from hub.helpers.dictionaries import Dictionaries
from hub.imports.construction_factory import ConstructionFactory
from hub.imports.geometry_factory import GeometryFactory
from hub.imports.results_factory import ResultFactory
from hub.imports.usage_factory import UsageFactory


class TestResultsImport(TestCase):
  """
  TestImports class contains the unittest for import functionality
  """
  def setUp(self) -> None:
    """
    Test setup
    :return: None
    """
    self._example_path = (Path(__file__).parent / 'tests_data').resolve()
    self._output_path = (Path(__file__).parent / 'tests_outputs').resolve()
    file = 'Citylayers_neighbours_simp2.json'
    file_path = (self._example_path / file).resolve()
    self._city = GeometryFactory('geojson',
                                 path=file_path,
                                 height_field='heightmax',
                                 year_of_construction_field='ANNEE_CONS',
                                 function_field='CODE_UTILI',
                                 function_to_hub=Dictionaries().montreal_function_to_hub_function).city

    ConstructionFactory('nrcan', self._city).enrich()
    UsageFactory('comnet', self._city).enrich()

  def test_sra_import(self):
    ExportsFactory('sra', self._city, self._output_path).export()
    sra_path = (self._output_path / f'{self._city.name}_sra.xml').resolve()
    subprocess.run(['sra', str(sra_path)])
    ResultFactory('sra', self._city, self._output_path).enrich()
    # Check that all the buildings have radiance in the surfaces
    for building in self._city.buildings:
      for surface in building.surfaces:
        self.assertIsNotNone(surface.global_irradiance)

  def test_meb_import(self):
    ExportsFactory('sra', self._city, self._output_path).export()
    sra_path = (self._output_path / f'{self._city.name}_sra.xml').resolve()
    subprocess.run(['sra', str(sra_path)])
    ResultFactory('sra', self._city, self._output_path).enrich()
    EnergyBuildingsExportsFactory('insel_monthly_energy_balance', self._city, self._output_path).export()
    for building in self._city.buildings:
      insel_path = (self._output_path / f'{building.name}.insel')
      subprocess.run(['insel', str(insel_path)])
    ResultFactory('insel_monthly_energy_balance', self._city, self._output_path).enrich()
    # Check that all the buildings have heating and cooling values
    for building in self._city.buildings:
      self.assertIsNotNone(building.heating_demand[cte.MONTH])
      self.assertIsNotNone(building.cooling_demand[cte.MONTH])
      self.assertIsNotNone(building.heating_demand[cte.YEAR])
      self.assertIsNotNone(building.cooling_demand[cte.YEAR])
      self.assertIsNotNone(building.lighting_peak_load[cte.MONTH])
      self.assertIsNotNone(building.lighting_peak_load[cte.YEAR])
      self.assertIsNotNone(building.appliances_peak_load[cte.MONTH])
      self.assertIsNotNone(building.appliances_peak_load[cte.YEAR])

  def test_peak_loads(self):
    # todo: this is not technically a import
    ExportsFactory('sra', self._city, self._output_path).export()
    sra_path = (self._output_path / f'{self._city.name}_sra.xml').resolve()
    subprocess.run(['sra', str(sra_path)])
    ResultFactory('sra', self._city, self._output_path).enrich()
    for building in self._city.buildings:
      self.assertIsNotNone(building.heating_peak_load)
      self.assertIsNotNone(building.cooling_peak_load)

    values = [0 for _ in range(8760)]
    values[0] = 1000
    expected_monthly_list = [0 for _ in range(12)]
    expected_monthly_list[0] = 1000
    for building in self._city.buildings:
      building.heating_demand[cte.HOUR] = values
      building.cooling_demand[cte.HOUR] = values
      self.assertIsNotNone(building.heating_peak_load)
      self.assertIsNotNone(building.cooling_peak_load)
