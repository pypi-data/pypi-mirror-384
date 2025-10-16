"""
TestMultizoneExports test and validate the city export formats when using multizone for buildings
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2022 Concordia CERC group
Project Coder Guille Gutierrez guillermo.gutierrezmorote@concordia.ca
"""
from pathlib import Path
from unittest import TestCase

import hub.helpers.constants as cte
from hub.city_model_structure.building import Building
from hub.exports.energy_building_exports_factory import EnergyBuildingsExportsFactory
from hub.helpers.dictionaries import Dictionaries
from hub.imports.construction_factory import ConstructionFactory
from hub.imports.geometry_factory import GeometryFactory
from hub.imports.results_factory import ResultFactory
from hub.imports.usage_factory import UsageFactory
from hub.imports.weather_factory import WeatherFactory


class TestMultizoneExports(TestCase):
  """
  TestExports class contains the unittest for export functionality
  """

  def setUp(self) -> None:
    """
    Test setup
    :return: None
    """
    self._city = None
    self._complete_city = None
    self._example_path = (Path(__file__).parent / 'tests_data').resolve()
    self._output_path = (Path(__file__).parent / 'tests_outputs').resolve()


  def building(self, city, building) -> Building:
    return city.city_object(building.name)

  def test_floor_area(self):
    file = 'Citylayers_neighbours_simp2.json'
    file_path = (self._example_path / file).resolve()
    city_multizone = GeometryFactory('geojson',
                           path=file_path,
                           height_field='heightmax',
                           year_of_construction_field='ANNEE_CONS',
                           function_field='CODE_UTILI',
                           storey_height_field='ETAGE_HORS',
                           function_to_hub=Dictionaries().montreal_function_to_hub_function).city
    self.assertIsNotNone(city_multizone, 'city is none')
    ConstructionFactory('nrcan', city_multizone).enrich()
    UsageFactory('nrcan', city_multizone).enrich()
    WeatherFactory('epw', city_multizone).enrich()

    city_single_zone = GeometryFactory('geojson',
                                     path=file_path,
                                     height_field='heightmax',
                                     year_of_construction_field='ANNEE_CONS',
                                     function_field='CODE_UTILI',
                                     function_to_hub=Dictionaries().montreal_function_to_hub_function).city
    self.assertIsNotNone(city_single_zone, 'city is none')
    ConstructionFactory('nrcan', city_single_zone).enrich()
    UsageFactory('nrcan', city_single_zone).enrich()
    WeatherFactory('epw', city_single_zone).enrich()

    for building_singlezone in city_single_zone.buildings:
      building_multizone = self.building(city_multizone, building_singlezone)
      self.assertEqual (building_singlezone.floor_area, building_multizone.floor_area, 'floor area is not the same')
      self.assertEqual(building_singlezone.total_floor_area, building_multizone.total_floor_area, 'total floor area is not the same')


  def test_multizone_cerc_idf_export(self):
    """
    export to IDF
    """
    file = 'Citylayers_neighbours_simp2.json'
    file_path = (self._example_path / file).resolve()
    city = GeometryFactory('geojson',
                           path=file_path,
                           height_field='heightmax',
                           year_of_construction_field='ANNEE_CONS',
                           function_field='CODE_UTILI',
                           storey_height_field='ETAGE_HORS',
                           function_to_hub=Dictionaries().montreal_function_to_hub_function).city
    self.assertIsNotNone(city, 'city is none')
    ConstructionFactory('nrcan', city).enrich()
    UsageFactory('nrcan', city).enrich()
    WeatherFactory('epw', city).enrich()
    idf = EnergyBuildingsExportsFactory('cerc_idf', city, self._output_path).export()
    idf.run()
    csv_output_path = (self._output_path / f'{city.name}_out.csv').resolve()
    self.assertTrue(csv_output_path.is_file())
    ResultFactory('cerc_idf', city, csv_output_path).enrich()
    for building in city.buildings:
      self.assertIsNotNone(building.heating_demand)
      self.assertIsNotNone(building.cooling_demand)
      self.assertIsNotNone(building.domestic_hot_water_heat_demand)
      self.assertIsNotNone(building.lighting_electrical_demand)
      self.assertIsNotNone(building.appliances_electrical_demand)
      heating = 0
      cooling = 0
      dhw = 0
      appliances = 0
      lighting = 0
      print(building.total_floor_area, building.floor_area,  building.storeys_above_ground)
      for zone in building.internal_zones:
        self.assertIsNotNone(zone.heating_demand)
        self.assertIsNotNone(zone.cooling_demand)
        self.assertIsNotNone(zone.domestic_hot_water_heat_demand)
        self.assertIsNotNone(zone.lighting_electrical_demand)
        self.assertIsNotNone(zone.appliances_electrical_demand)
        heating += zone.heating_demand[cte.YEAR][0]
        cooling += zone.cooling_demand[cte.YEAR][0]
        dhw += zone.domestic_hot_water_heat_demand[cte.YEAR][0]
        appliances += zone.appliances_electrical_demand[cte.YEAR][0]
        lighting += zone.lighting_electrical_demand[cte.YEAR][0]
        for period in cte.PERIODS:
          self.assertAlmostEqual(zone.heating_demand[cte.YEAR][0], sum(zone.heating_demand[period]), 1,
                                 f'{period} values per zone doesn\'t match')
          self.assertAlmostEqual(zone.cooling_demand[cte.YEAR][0], sum(zone.cooling_demand[period]), 1,
                                 f'{period} values per zone doesn\'t match')
          self.assertAlmostEqual(zone.domestic_hot_water_heat_demand[cte.YEAR][0],
                                 sum(zone.domestic_hot_water_heat_demand[period]), 1,
                                 f'{period} values per zone doesn\'t match')
          self.assertAlmostEqual(zone.appliances_electrical_demand[cte.YEAR][0],
                                 sum(zone.appliances_electrical_demand[period]), 1,
                                 f'{period} values per zone doesn\'t match')
          self.assertAlmostEqual(zone.lighting_electrical_demand[cte.YEAR][0],
                                 sum(zone.lighting_electrical_demand[period]), 1,
                                 f'{period} values per zone doesn\'t match')

      for period in cte.PERIODS:
        self.assertAlmostEqual(sum(building.heating_demand[period]), heating, 1, f'{period} values doesn\'t match')
        self.assertAlmostEqual(sum(building.cooling_demand[period]), cooling, 1, f'{period} values doesn\'t match')
        self.assertAlmostEqual(sum(building.domestic_hot_water_heat_demand[period]), dhw, 1,
                               f'{period} values doesn\'t match')
        self.assertAlmostEqual(sum(building.appliances_electrical_demand[period]), appliances, 1,
                               f'{period} values doesn\'t match')
        self.assertAlmostEqual(sum(building.lighting_electrical_demand[period]), lighting, 1,
                               f'{period} values doesn\'t match')
