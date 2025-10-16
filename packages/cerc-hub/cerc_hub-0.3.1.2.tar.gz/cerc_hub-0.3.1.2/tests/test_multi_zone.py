"""
TestGeometryFactory test and validate the city model structure geometric parameters
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2022 Concordia CERC group
Project Coder Guille Gutierrez guillermo.gutierrezmorote@concordia.ca
"""
import glob
import subprocess
from argparse import ArgumentError
from pathlib import Path
from unittest import TestCase

from hub.exports.energy_building_exports_factory import EnergyBuildingsExportsFactory
from hub.exports.exports_factory import ExportsFactory
from hub.helpers.dictionaries import Dictionaries
from hub.imports.construction_factory import ConstructionFactory
from hub.imports.energy_systems_factory import EnergySystemsFactory
from hub.imports.geometry_factory import GeometryFactory
from hub.imports.results_factory import ResultFactory
from hub.imports.usage_factory import UsageFactory
from hub.imports.weather_factory import WeatherFactory


class TestMultiZone(TestCase):

  def setUp(self) -> None:
    """
    Test setup
    :return: None
    """
    self._city = None
    self._example_path = (Path(__file__).parent / 'tests_data').resolve()
    self._output_path = (Path(__file__).parent / 'tests_outputs').resolve()

  def _get_city(self, file, file_type, height_field=None, year_of_construction_field=None, function_field=None):
    file_path = (self._example_path / file).resolve()
    self._city = GeometryFactory(file_type,
                                 path=file_path,
                                 height_field=height_field,
                                 year_of_construction_field=year_of_construction_field,
                                 function_field=function_field,
                                 function_to_hub=Dictionaries().montreal_function_to_hub_function
                                 ).city
    self.assertIsNotNone(self._city, 'city is none')
    return self._city

  def test_import_geojson_with_storeys(self):

    """
    Test geojson import with ETAGE_HORS
    """
    file = Path(self._example_path / 'Citylayers_neighbours_simp2.json').resolve()
    city = GeometryFactory('geojson',
                           path=file,
                           height_field='heightmax',
                           year_of_construction_field='ANNEE_CONS',
                           aliases_field=['ID_UEV', 'CIVIQUE_DE', 'NOM_RUE'],
                           function_field='CODE_UTILI',
                           storey_height_field='ETAGE_HORS',
                           function_to_hub=Dictionaries().montreal_function_to_hub_function).city

    for building in city.buildings:
      zones = len(building.internal_zones)
      building.energy_systems = ['system 1 gas']
      building.energy_systems_archetype_name = building.energy_systems[0]
      self.assertTrue(len(building.internal_zones) > 1, f'building {building.name}({building.storeys_above_ground}) has too few internal zones {zones}')
      print(building.name, building.storeys_above_ground, building.max_height, building.average_storey_height)
    ConstructionFactory('nrcan', city).enrich()
    UsageFactory('nrcan', city).enrich()
    WeatherFactory('epw', city).enrich()
    ExportsFactory('obj',  city, self._output_path).export()
    ExportsFactory('sra', city, self._output_path).export()
    sra_file = Path(f'{self._output_path}/{city.name}_sra.xml').resolve()
    subprocess.run(["sra", sra_file],
                   capture_output=True,
                   check=True)
    ResultFactory('sra', city, self._output_path).enrich()
    EnergySystemsFactory('montreal_custom', city).enrich()
    EnergyBuildingsExportsFactory('insel_monthly_energy_balance', city, self._output_path).export()
    insel_files = glob.glob(f'{self._output_path}/*.insel')
    for insel_file in insel_files:
      subprocess.run(['insel', str(insel_file)], stdout=subprocess.DEVNULL)

    ResultFactory('insel_monthly_energy_balance', city, self._output_path).enrich()

  def test_import_geojson_with_storeys_enrichments(self):

    """
    Test geojson import with ETAGE_HORS
    """
    file = Path(self._example_path / 'Citylayers_neighbours_simp2.json').resolve()
    city = GeometryFactory('geojson',
                           path=file,
                           height_field='heightmax',
                           year_of_construction_field='ANNEE_CONS',
                           aliases_field=['ID_UEV', 'CIVIQUE_DE', 'NOM_RUE'],
                           function_field='CODE_UTILI',
                           storey_height_field='ETAGE_HORS',
                           function_to_hub=Dictionaries().montreal_function_to_hub_function).city

    ConstructionFactory('nrcan', city).enrich()
    UsageFactory('nrcan', city).enrich()

    ConstructionFactory('nrel', city).enrich()
    UsageFactory('comnet', city).enrich()

    city.climate_reference_city = 'Palma'
    ConstructionFactory('palma', city).enrich()
    UsageFactory('palma', city).enrich()

    city.climate_reference_city = 'Eilat'
    ConstructionFactory('eilat', city).enrich()
    UsageFactory('eilat', city).enrich()
    for building in city.buildings:
      self.assertTrue(len(building.internal_zones) > 1, f'building {building.name} has too few internal zones')
      self.assertEqual(len(building.internal_zones), building.storeys_above_ground,
                       f'building {building.name} wrong number of internal zones')

