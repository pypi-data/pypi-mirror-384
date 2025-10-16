"""
TestUsageFactory test and validate the city model structure usage parameters
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2022 Concordia CERC group
Project Coder Pilar Monsalvete Alvarez de Uribarri pilar.monsalvete@concordia.ca
"""
from pathlib import Path
from unittest import TestCase

from hub.imports.geometry_factory import GeometryFactory
from hub.imports.construction_factory import ConstructionFactory
from hub.imports.usage_factory import UsageFactory
from hub.helpers.dictionaries import Dictionaries
from hub.helpers.usage_parsers import UsageParsers


class TestUsageFactory(TestCase):
  """
  TestUsageFactory TestCase
  """
  def setUp(self) -> None:
    """
    Configure test environment
    :return:
    """
    self._city = None
    self._example_path = (Path(__file__).parent / 'tests_data').resolve()

  def _get_citygml(self, file):
    file_path = (self._example_path / file).resolve()
    self._city = GeometryFactory('citygml', path=file_path).city
    self.assertIsNotNone(self._city, 'city is none')
    return self._city

  def _check_buildings(self, city):
    for building in city.buildings:
      self.assertIsNotNone(building.name, 'building name is none')
      self.assertIsNotNone(building.type, 'building type is none')
      self.assertIsNotNone(building.volume, 'building volume is none')
      self.assertIsNotNone(building.detailed_polyhedron, 'building detailed polyhedron is none')
      self.assertIsNotNone(building.simplified_polyhedron, 'building simplified polyhedron is none')
      self.assertIsNotNone(building.surfaces, 'building surfaces is none')
      self.assertIsNotNone(building.centroid, 'building centroid is none')
      self.assertIsNotNone(building.max_height, 'building max_height is none')
      self.assertEqual(len(building.external_temperature), 0, 'building external temperature is calculated')
      self.assertEqual(len(building.global_horizontal), 0, 'building global horizontal is calculated')
      self.assertEqual(len(building.diffuse), 0, 'building diffuse is calculated')
      self.assertEqual(len(building.beam), 0, 'building beam is calculated')
      self.assertIsNotNone(building.lower_corner, 'building lower corner is none')
      self.assertEqual(len(building.sensors), 0, 'building sensors are assigned')
      self.assertIsNotNone(building.internal_zones, 'no internal zones created')
      self.assertIsNotNone(building.grounds, 'building grounds is none')
      self.assertIsNotNone(building.walls, 'building walls is none')
      self.assertIsNotNone(building.roofs, 'building roofs is none')
      for internal_zone in building.internal_zones:
        if internal_zone.usages is not None:
          self.assertTrue(len(internal_zone.usages) > 0, 'usage zones are not defined')
      self.assertIsNone(building.basement_heated, 'building basement_heated is not none')
      self.assertIsNone(building.attic_heated, 'building attic_heated is not none')
      self.assertIsNone(building.terrains, 'building terrains is not none')
      self.assertIsNotNone(building.year_of_construction, 'building year_of_construction is none')
      self.assertIsNotNone(building.function, 'building function is none')
      self.assertEqual(len(building.heating_demand), 0, 'building heating is not none')
      self.assertEqual(len(building.cooling_demand), 0, 'building cooling is not none')
      self.assertIsNotNone(building.eave_height, 'building eave height is none')
      self.assertIsNotNone(building.roof_type, 'building roof type is none')
      self.assertIsNotNone(building.floor_area, 'building floor_area is none')

  def _check_usage(self, usage):
    self.assertIsNotNone(usage.name, 'usage is none')
    self.assertIsNotNone(usage.percentage, 'usage percentage is none')
    self.assertIsNotNone(usage.hours_day, 'hours per day is none')
    self.assertIsNotNone(usage.days_year, 'days per year is none')
    self.assertIsNotNone(usage.thermal_control, 'thermal control is none')
    self.assertIsNotNone(usage.thermal_control.mean_heating_set_point, 'control heating set point is none')
    self.assertIsNotNone(usage.thermal_control.heating_set_back, 'control heating set back is none')
    self.assertIsNotNone(usage.thermal_control.mean_cooling_set_point, 'control cooling set point is none')

    self.assertIsNotNone(usage.mechanical_air_change, 'mechanical air change is none')
    self.assertIsNotNone(usage.thermal_control.heating_set_point_schedules,
                         'control heating set point schedule is none')
    self.assertIsNotNone(usage.thermal_control.cooling_set_point_schedules,
                         'control cooling set point schedule is none')
    self.assertIsNotNone(usage.occupancy, 'occupancy is none')
    occupancy = usage.occupancy
    self.assertIsNotNone(occupancy.occupancy_density, 'occupancy density is none')
    self.assertIsNotNone(occupancy.latent_internal_gain, 'occupancy latent internal gain is none')
    self.assertIsNotNone(occupancy.sensible_convective_internal_gain,
                         'occupancy sensible convective internal gain is none')
    self.assertIsNotNone(occupancy.sensible_radiative_internal_gain,
                         'occupancy sensible radiant internal gain is none')
    self.assertIsNotNone(occupancy.occupancy_schedules, 'occupancy schedule is none')
    self.assertIsNotNone(usage.lighting, 'lighting is none')
    lighting = usage.lighting
    self.assertIsNotNone(lighting.density, 'lighting density is none')
    self.assertIsNotNone(lighting.latent_fraction, 'lighting latent fraction is none')
    self.assertIsNotNone(lighting.convective_fraction, 'lighting convective fraction is none')
    self.assertIsNotNone(lighting.radiative_fraction, 'lighting radiant fraction is none')
    self.assertIsNotNone(lighting.schedules, 'lighting schedule is none')
    self.assertIsNotNone(usage.appliances, 'appliances is none')
    appliances = usage.appliances
    self.assertIsNotNone(appliances.density, 'appliances density is none')
    self.assertIsNotNone(appliances.latent_fraction, 'appliances latent fraction is none')
    self.assertIsNotNone(appliances.convective_fraction, 'appliances convective fraction is none')
    self.assertIsNotNone(appliances.radiative_fraction, 'appliances radiant fraction is none')
    self.assertIsNotNone(appliances.schedules, 'appliances schedule is none')
    self.assertIsNotNone(usage.thermal_control.hvac_availability_schedules,
                         'control hvac availability is none')
    self.assertIsNotNone(usage.domestic_hot_water.service_temperature,
                         'domestic hot water service temperature is none')
    self.assertIsNotNone(usage.domestic_hot_water.schedules, 'domestic hot water schedules is none')

  def test_import_comnet(self):
    """
    Enrich the city with the usage information from comnet and verify it
    """
    file = 'pluto_building.gml'
    city = self._get_citygml(file)
    for building in city.buildings:
      building.function = Dictionaries().pluto_function_to_hub_function[building.function]

    UsageFactory('comnet', city).enrich()
    self._check_buildings(city)
    for building in city.buildings:
      for internal_zone in building.internal_zones:
        self.assertIsNot(len(internal_zone.usages), 0, 'no building usage defined')
        for usage in internal_zone.usages:
          self._check_usage(usage)
          self.assertIsNotNone(usage.domestic_hot_water.density, 'domestic hot water density is none')

  def test_import_nrcan(self):
    """
    Enrich the city with the usage information from nrcan and verify it
    """
    file = 'test.geojson'
    file_path = (self._example_path / file).resolve()
    city = GeometryFactory('geojson',
                           path=file_path,
                           height_field='citygml_me',
                           year_of_construction_field='ANNEE_CONS',
                           function_field='CODE_UTILI',
                           function_to_hub=Dictionaries().montreal_function_to_hub_function).city

    ConstructionFactory('nrcan', city).enrich()
    UsageFactory('nrcan', city).enrich()
    self._check_buildings(city)
    for building in city.buildings:
      for internal_zone in building.internal_zones:
        if internal_zone.usages is not None:
          self.assertIsNot(len(internal_zone.usages), 0, 'no building usage defined')
          for usage in internal_zone.usages:
            self._check_usage(usage)
  
  def test_import_palma(self):
    """
    Enrich the city with the usage information from palma and verify it
    """
    file = 'palma_test_file.geojson'
    file_path = (self._example_path / file).resolve()
    city = GeometryFactory('geojson',
                           path=file_path,
                           height_field='measuredHeight',
                           year_of_construction_field='yearOfConstruction',
                           function_field='usage',
                           function_to_hub=Dictionaries().palma_function_to_hub_function).city

    ConstructionFactory('palma', city).enrich()
    UsageFactory('palma', city).enrich()
    self._check_buildings(city)
    for building in city.buildings:
      for internal_zone in building.internal_zones:
        if internal_zone.usages is not None:
          self.assertIsNot(len(internal_zone.usages), 0, 'no building usage defined')
          for usage in internal_zone.usages:
            self._check_usage(usage)
            self.assertIsNotNone(usage.domestic_hot_water.peak_flow, 'domestic hot water peak flow is none')



  def test_import_nrcan_multiusage(self):
    """
    Enrich the city with the usage information from nrcan and verify it
    """
    file = 'test.geojson'
    file_path = (self._example_path / file).resolve()

    function_dictionary = Dictionaries().montreal_function_to_hub_function
    usage_parser = UsageParsers().list_usage_to_hub(function_dictionary=function_dictionary)

    city = GeometryFactory('geojson',
                           path=file_path,
                           height_field='citygml_me',
                           year_of_construction_field='ANNEE_CONS',
                           function_field='CODE_UTILI',
                           function_to_hub=function_dictionary,
                           usages_field='usages',
                           usages_to_hub=usage_parser).city

    ConstructionFactory('nrcan', city).enrich()
    UsageFactory('nrcan', city).enrich()
    self._check_buildings(city)
    for building in city.buildings:
      for internal_zone in building.internal_zones:
        if internal_zone.usages is not None:
          self.assertIsNot(len(internal_zone.usages), 0, 'no building usage defined')
          for usage in internal_zone.usages:
            self._check_usage(usage)
