"""
TestExports test and validate the city export formats
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2022 Concordia CERC group
Project Coder Guille Gutierrez guillermo.gutierrezmorote@concordia.ca
Code contributors: Pilar Monsalvete Alvarez de Uribarri pilar.monsalvete@concordia.ca
"""
import json
import os
from pathlib import Path
from unittest import TestCase

import hub.helpers.constants as cte
from hub.city_model_structure.city import City
from hub.exports.energy_building_exports_factory import EnergyBuildingsExportsFactory
from hub.exports.exports_factory import ExportsFactory
from hub.helpers.dictionaries import Dictionaries
from hub.imports.construction_factory import ConstructionFactory
from hub.imports.geometry_factory import GeometryFactory
from hub.imports.results_factory import ResultFactory
from hub.imports.usage_factory import UsageFactory
from hub.imports.weather_factory import WeatherFactory


class TestExports(TestCase):
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

  def _get_citygml(self, file):
    file_path = (self._example_path / file).resolve()
    self._city = GeometryFactory('citygml', path=file_path).city
    self.assertIsNotNone(self._city, 'city is none')
    return self._city

  def _get_complete_city(self, from_pickle):
    if self._complete_city is None:
      if from_pickle:
        file_path = (self._example_path / 'ConcordiaSWGcampus.pickle').resolve()
        self._complete_city = City.load(file_path)
      else:
        file_path = (self._example_path / 'one_building_in_kelowna.gml').resolve()
        self._complete_city = self._get_citygml(file_path)
        for building in self._complete_city.buildings:
          building.function = Dictionaries().hft_function_to_hub_function[building.function]
          building.year_of_construction = 2006
        ConstructionFactory('nrel', self._complete_city).enrich()
        UsageFactory('nrcan', self._complete_city).enrich()
        cli = (self._example_path / 'weather' / 'inseldb_Summerland.cli').resolve()
        self._complete_city.climate_file = Path(cli)
        self._complete_city.climate_reference_city = 'Summerland'
        dummy_measures = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        for building in self._complete_city.buildings:
          building.heating_demand[cte.MONTH] = dummy_measures
          building.cooling_demand[cte.MONTH] = dummy_measures
          building.heating_demand[cte.YEAR] = [0.0]
          building.cooling_demand[cte.YEAR] = [0.0]
    return self._complete_city

  def _export(self, export_type, from_pickle=False):
    self._complete_city = self._get_complete_city(from_pickle)
    ExportsFactory(export_type, self._complete_city, self._output_path, base_uri='../glb').export()

  def _export_building_energy(self, export_type, from_pickle=False):
      self._complete_city = self._get_complete_city(from_pickle)
      EnergyBuildingsExportsFactory(export_type, self._complete_city, self._output_path).export()

  def test_obj_export(self):
    """
    export to obj
    """
    self._export('obj', False)

  def test_cesiumjs_tileset_export(self):
    """
    export to cesiumjs tileset
    """
    self._export('cesiumjs_tileset', False)
    tileset = Path(self._output_path / f'{self._city.name}.json')
    self.assertTrue(tileset.exists())
    with open(tileset, 'r') as f:
      json_tileset = json.load(f)
    self.assertEqual(1, len(json_tileset['root']['children']), "Wrong number of children")

  def test_glb_export(self):
    """
    export to glb format
    """
    self._export('glb', False)
    for building in self._city.buildings:
      glb_file = Path(self._output_path / f'{building.name}.glb')
      self.assertTrue(glb_file.exists(), f'{building.name} Building glb wasn\'t correctly generated')

  def test_geojson_export(self):
    self._export('geojson', False)
    geojson_file = Path(self._output_path / f'{self._city.name}.geojson')
    self.assertTrue(geojson_file.exists(), f'{geojson_file} doesn\'t exists')
    with open(geojson_file, 'r') as f:
      geojson = json.load(f)
    self.assertEqual(1, len(geojson['features']), 'Wrong number of buildings')
    geometry = geojson['features'][0]['geometry']
    self.assertEqual('Polygon', geometry['type'], 'Wrong geometry type')
    self.assertEqual(1, len(geometry['coordinates']), 'Wrong polygon structure')
    self.assertEqual(11, len(geometry['coordinates'][0]), 'Wrong number of vertices')
    os.unlink(geojson_file)  # todo: this test need to cover a multipolygon example too

  def test_energy_ade_export(self):
    """
    export to energy ADE
    """
    self._export_building_energy('energy_ade')

  def test_sra_export(self):
    """
    export to SRA
    """
    self._export('sra')

  def test_idf_export(self):
    """
    export to IDF
    """
    file = 'test.geojson'
    file_path = (self._example_path / file).resolve()

    city = GeometryFactory('geojson',
                           path=file_path,
                           height_field='citygml_me',
                           year_of_construction_field='ANNEE_CONS',
                           function_field='CODE_UTILI',
                           function_to_hub=Dictionaries().montreal_function_to_hub_function).city
    self.assertIsNotNone(city, 'city is none')
    ConstructionFactory('nrcan', city).enrich()
    UsageFactory('nrcan', city).enrich()
    WeatherFactory('epw', city).enrich()
    # todo: reintroduce the pure geometry cases this test in cerc_idf
    try:
      _idf = EnergyBuildingsExportsFactory('idf', city, self._output_path).export()
      _idf.run()
      city.name = f'{city.name}_simplified'
      custom_outputs = {
        'control_files': ['CSV'],
        "output_meters": [
          {"name": "districtheating:facility", "frequency": "monthly"},
          {"name": "interiorequipment:electricity", "frequency": "hourly"}
        ],
        "output_variables": [
          {"key_value": "*",
           "name": "zone ideal loads supply air total heating energy",
           "frequency": "hourly"}
        ]
      }
      _idf = EnergyBuildingsExportsFactory('idf', city, self._output_path, outputs=custom_outputs).export()
      _idf.run()
    except Exception:
      self.fail("Idf ExportsFactory raised ExceptionType unexpectedly!")

  def test_cerc_idf_export(self):
    """
    export to IDF
    """
    file = 'test.geojson'
    file_path = (self._example_path / file).resolve()
    city = GeometryFactory('geojson',
                           path=file_path,
                           height_field='citygml_me',
                           year_of_construction_field='ANNEE_CONS',
                           function_field='CODE_UTILI',
                           function_to_hub=Dictionaries().montreal_function_to_hub_function).city
    self.assertIsNotNone(city, 'city is none')
    ConstructionFactory('nrcan', city).enrich()
    UsageFactory('nrcan', city).enrich()
    WeatherFactory('epw', city).enrich()
    try:
      idf = EnergyBuildingsExportsFactory('cerc_idf', city, self._output_path).export()
      idf.run()
      csv_output_path = (self._output_path / f'{city.name}_out.csv').resolve()
      ResultFactory('cerc_idf', city, csv_output_path).enrich()
      self.assertTrue(csv_output_path.is_file())
      for building in city.buildings:
        self.assertIsNotNone(building.heating_demand)
        self.assertIsNotNone(building.cooling_demand)
        self.assertIsNotNone(building.domestic_hot_water_heat_demand)
        self.assertIsNotNone(building.lighting_electrical_demand)
        self.assertIsNotNone(building.appliances_electrical_demand)
        total_demand = sum(building.heating_demand[cte.HOUR])
        total_demand_month = sum(building.heating_demand[cte.MONTH])
        self.assertAlmostEqual(total_demand, building.heating_demand[cte.YEAR][0], 1)
        self.assertAlmostEqual(total_demand_month, building.heating_demand[cte.YEAR][0], 1)
    except Exception:
      self.fail("Idf ExportsFactory raised ExceptionType unexpectedly!")
