"""
TestCo2AnalysisFactory tests the calculation and assignment of co2 emissions to buildings by catalog
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2019 - 2025 Concordia CERC group
Project Koa Wells kekoa.wells@concordia.ca
"""

from unittest import TestCase
from pathlib import Path

import hub.helpers.constants as cte
from hub.imports.co2_analysis_factory import Co2AnalysisFactory
from hub.imports.geometry_factory import GeometryFactory
from hub.imports.construction_factory import ConstructionFactory
from hub.helpers.dictionaries import Dictionaries

class TestCo2AnalysisFactory(TestCase):
  """
  TestCo2AnalysisFactory TestCase
  """
  def setUp(self) -> None:
    """
    Setup test environment
    """
    self._test_data_path = Path(__file__).parent / 'tests_data'

  def test_ecoinvent_co2_analysis_factory(self):
    """
    Tests the calculation of co2 emissions for buildings using the hub catalog
    """
    city = GeometryFactory('geojson',
                           self._test_data_path / 'test.geojson',
                           year_of_construction_field='ANNEE_CONS',
                           function_field='CODE_UTILI',
                           height_field='citygml_me',
                           function_to_hub=Dictionaries().montreal_function_to_hub_function).city
    ConstructionFactory('nrcan', city).enrich()
    Co2AnalysisFactory('ecoinvent', city).enrich()
    for building in city.buildings:
      self.assertIsNotNone(building.embodied_co2, 'No embodied CO2 emissions found assigned to building')
      self.assertIsNotNone(building.end_of_life_co2, 'No end-of-life CO2 emissions found assigned to building')
      self.assertGreater(building.embodied_co2[cte.ENVELOPE_CO2], 0, 'No envelope embodied CO2 emissions found assigned to building')
      self.assertGreater(building.end_of_life_co2[cte.ENVELOPE_CO2], 0,  'No envelope end-of-life CO2 emissions found assigned to building')
      self.assertGreater(building.embodied_co2[cte.OPENING_CO2], 0,  'No opening embodied CO2 emissions found assigned to building')
      self.assertGreater(building.end_of_life_co2[cte.OPENING_CO2], 0,  'No opening end-of-life CO2 emissions found assigned to building')
