"""
TestCityMerge test and validate the merge of several cities into one
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2022 Concordia CERC group
Project Coder Guille Gutierrez Guillermo.GutierrezMorote@concordia.ca
"""

import copy
import distutils.spawn
import subprocess
from pathlib import Path
from unittest import TestCase

from hub.city_model_structure.city import City
from hub.imports.geometry_factory import GeometryFactory
from hub.imports.results_factory import ResultFactory
from hub.exports.exports_factory import ExportsFactory
import hub.helpers.constants as cte


class TestCityMerge(TestCase):
  """
  Functional TestCityMerge
  """
  def setUp(self) -> None:
    """
    Test setup
    :return: None
    """
    self._example_path = (Path(__file__).parent / 'tests_data').resolve()
    self._output_path = (Path(__file__).parent / 'tests_outputs').resolve()
    self._executable = 'sra'

  def test_merge(self):
    file_path = Path(self._example_path / 'test.geojson').resolve()
    full_city = GeometryFactory('geojson', file_path, height_field='citygml_me').city
    self.assertEqual(17, len(full_city.buildings), 'Wrong number of buildings')
    odd_city = City(full_city.lower_corner, full_city.upper_corner, full_city.srs_name)
    even_city = City(full_city.lower_corner, full_city.upper_corner, full_city.srs_name)
    for building in full_city.buildings:
      if int(building.name) % 2 == 0:
        even_city.add_city_object(copy.deepcopy(building))
      else:
        odd_city.add_city_object(copy.deepcopy(building))
    self.assertEqual(8, len(odd_city.buildings), 'Wrong number of odd buildings')
    self.assertEqual(9, len(even_city.buildings), 'Wrong number of par buildings')
    merged_city = odd_city.merge(even_city)
    self.assertEqual(17, len(merged_city.buildings), 'Wrong number of buildings in merged city')
    merged_city = even_city.merge(odd_city)
    self.assertEqual(17, len(merged_city.buildings), 'Wrong number of buildings in merged city')
    merged_city = full_city.merge(odd_city).merge(even_city)
    self.assertEqual(17, len(merged_city.buildings), 'Wrong number of buildings in merged city')

  def test_merge_with_radiation(self):
    sra = distutils.spawn.find_executable('sra')
    file_path = Path(self._example_path / 'test.geojson').resolve()

    full_city = GeometryFactory('geojson', file_path, height_field='citygml_me').city
    even_city = City(full_city.lower_corner, full_city.upper_corner, full_city.srs_name)
    for building in full_city.buildings:
      if int(building.name) % 2 == 0:
        even_city.add_city_object(copy.deepcopy(building))
    ExportsFactory('sra', full_city, self._output_path).export()
    sra_file = str((self._output_path / f'{full_city.name}_sra.xml').resolve())
    subprocess.run([sra, sra_file], stdout=subprocess.DEVNULL)
    ResultFactory('sra', full_city, self._output_path).enrich()
    self.assertEqual(17, len(full_city.buildings), 'Wrong number of buildings')
    merged_city = full_city.merge(even_city)

    full_city_building_total_radiation = 0
    for building in merged_city.buildings:
      for surface in building.surfaces:
        if surface.global_irradiance:
          full_city_building_total_radiation += surface.global_irradiance[cte.YEAR][0]

    merged_city_building_total_radiation = 0
    for building in merged_city.buildings:
      for surface in building.surfaces:
        if surface.global_irradiance:
          merged_city_building_total_radiation += surface.global_irradiance[cte.YEAR][0]
    self.assertEqual(full_city_building_total_radiation, merged_city_building_total_radiation)

    merged_city = even_city.merge(full_city)
    merged_city_building_total_radiation = 0
    for building in merged_city.buildings:
      for surface in building.surfaces:
        if surface.global_irradiance:
          merged_city_building_total_radiation += surface.global_irradiance[cte.YEAR][0]
    self.assertEqual(full_city_building_total_radiation, merged_city_building_total_radiation)

    for building in even_city.buildings:
      for surface in building.surfaces:
        surface.global_irradiance[cte.YEAR] = [3]

    merged_city = full_city.merge(even_city)
    first_merged_city_building_total_radiation = 0
    for building in merged_city.buildings:
      for surface in building.surfaces:
        if surface.global_irradiance:
          first_merged_city_building_total_radiation += surface.global_irradiance[cte.YEAR][0]
    merged_city = even_city.merge(full_city)
    second_merged_city_building_total_radiation = 0
    for building in merged_city.buildings:
      for surface in building.surfaces:
        if surface.global_irradiance:
          second_merged_city_building_total_radiation += surface.global_irradiance[cte.YEAR][0]
    self.assertAlmostEqual(first_merged_city_building_total_radiation, second_merged_city_building_total_radiation, 8)

