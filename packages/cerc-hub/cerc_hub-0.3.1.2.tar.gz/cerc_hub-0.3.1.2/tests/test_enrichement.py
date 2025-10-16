"""
TestGeometryFactory test and validate the city model structure geometric parameters
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2022 Concordia CERC group
Project Coder Pilar Monsalvete Alvarez de Uribarri pilar.monsalvete@concordia.ca
"""
from pathlib import Path
from unittest import TestCase
from hub.imports.geometry_factory import GeometryFactory
from hub.helpers.dictionaries import Dictionaries
from hub.imports.usage_factory import UsageFactory
from hub.imports.construction_factory import ConstructionFactory


class TestGeometryFactory(TestCase):
  """
  Non-functional TestGeometryFactory
  Load testing
  """
  def setUp(self) -> None:
    """
    Test setup
    :return: None
    """
    self._city = None
    self._example_path = (Path(__file__).parent / 'tests_data').resolve()

  def _get_citygml(self, file):
    file_path = (self._example_path / file).resolve()
    self._city = GeometryFactory('citygml', path=file_path).city
    self.assertIsNotNone(self._city, 'city is none')
    return self._city

  def _check_result(self, city):
    self._check_buildings(city)
    for building in city.buildings:
      for internal_zone in building.internal_zones:
        self.assertIsNot(len(internal_zone.usages), 0, 'no building usages defined')
        for usage in internal_zone.usages:
          self.assertIsNotNone(usage.id, 'usage id is none')
        for thermal_zone in internal_zone.thermal_zones_from_internal_zones:
          self._check_thermal_zone(thermal_zone)

  def _check_buildings(self, city):
    for building in city.buildings:
      self.assertIsNotNone(building.internal_zones, 'no internal zones created')
      for internal_zone in building.internal_zones:
        self.assertIsNotNone(internal_zone.usages, 'usage zones are not defined')
        self.assertIsNotNone(internal_zone.thermal_zones_from_internal_zones, 'thermal zones are not defined')
      self.assertIsNone(building.basement_heated, 'building basement_heated is not none')
      self.assertIsNone(building.attic_heated, 'building attic_heated is not none')
      self.assertIsNotNone(building.average_storey_height, 'building average_storey_height is none')
      self.assertIsNotNone(building.storeys_above_ground, 'building storeys_above_ground is none')
      self.assertTrue(building.is_conditioned, 'building is_conditioned is not conditioned')

  def _check_thermal_zone(self, thermal_zone):
    self.assertIsNotNone(thermal_zone.id, 'thermal_zone id is none')
    self.assertIsNotNone(thermal_zone.usage_name, 'thermal_zone usage is not none')
    self.assertIsNotNone(thermal_zone.hours_day, 'thermal_zone hours a day is none')
    self.assertIsNotNone(thermal_zone.days_year, 'thermal_zone days a year is none')
    self.assertIsNotNone(thermal_zone.occupancy, 'thermal_zone occupancy is none')
    self.assertIsNotNone(thermal_zone.thermal_control, 'thermal_zone thermal control is none')
    self.assertIsNotNone(thermal_zone.internal_gains, 'thermal_zone internal gains returns none')

  def _check_extra_thermal_zone(self, thermal_zone):
    self.assertIsNotNone(thermal_zone.lighting, 'thermal_zone lighting is none')
    self.assertIsNotNone(thermal_zone.appliances, 'thermal_zone appliances is none')
    self.assertIsNotNone(thermal_zone.mechanical_air_change, 'thermal_zone mechanical air change is none')

  @staticmethod
  def _prepare_case_usage_first(city, input_key, construction_key, usage_key):
    if input_key == 'pluto':
      for building in city.buildings:
        building.function = Dictionaries().pluto_function_to_hub_function[building.function]
    elif input_key == 'hft':
      for building in city.buildings:
        building.function = Dictionaries().hft_function_to_hub_function[building.function]
    UsageFactory(usage_key, city).enrich()
    ConstructionFactory(construction_key, city).enrich()

  @staticmethod
  def _prepare_case_construction_first(city, input_key, construction_key, usage_key):
    if input_key == 'pluto':
      for building in city.buildings:
        building.function = Dictionaries().pluto_function_to_hub_function[building.function]
    elif input_key == 'hft':
      for building in city.buildings:
        building.function = Dictionaries().hft_function_to_hub_function[building.function]
    ConstructionFactory(construction_key, city).enrich()
    UsageFactory(usage_key, city).enrich()

  def _test_hft(self, file):
    _construction_keys = ['nrel']
    _usage_keys = ['comnet']
    for construction_key in _construction_keys:
      for usage_key in _usage_keys:
        # construction factory called first
        city = self._get_citygml(file)
        for building in city.buildings:
          building.year_of_construction = 2006
        self.assertTrue(len(city.buildings) > 0)
        self._prepare_case_construction_first(city, 'hft', construction_key, usage_key)
        self._check_result(city)
        if usage_key == 'comnet':
          for building in city.buildings:
            for internal_zone in building.internal_zones:
              for thermal_zone in internal_zone.thermal_zones_from_internal_zones:
                self._check_extra_thermal_zone(thermal_zone)
        # usage factory called first
        city = self._get_citygml(file)
        for building in city.buildings:
          building.year_of_construction = 2006
        self.assertTrue(len(city.buildings) > 0)
        self._prepare_case_usage_first(city, 'hft', construction_key, usage_key)
        self._check_result(city)
        if usage_key == 'comnet':
          for building in city.buildings:
            for internal_zone in building.internal_zones:
              for thermal_zone in internal_zone.thermal_zones_from_internal_zones:
                self._check_extra_thermal_zone(thermal_zone)

  def _test_pluto(self, file):
    _construction_keys = ['nrel']
    _usage_keys = ['comnet', 'nrcan']
    for construction_key in _construction_keys:
      for usage_key in _usage_keys:
        # construction factory called first
        city = self._get_citygml(file)
        for building in city.buildings:
          building.year_of_construction = 2006
        self.assertTrue(len(city.buildings) > 0)
        self._prepare_case_construction_first(city, 'pluto', construction_key, usage_key)
        self._check_result(city)
        if usage_key == 'comnet':
          for building in city.buildings:
            for internal_zone in building.internal_zones:
              for thermal_zone in internal_zone.thermal_zones_from_internal_zones:
                self._check_extra_thermal_zone(thermal_zone)
        # usage factory called first
        city = self._get_citygml(file)
        for building in city.buildings:
          building.year_of_construction = 2006
        self.assertTrue(len(city.buildings) > 0)
        self._prepare_case_usage_first(city, 'pluto', construction_key, usage_key)
        self._check_result(city)
        if usage_key == 'comnet':
          for building in city.buildings:
            for internal_zone in building.internal_zones:
              for thermal_zone in internal_zone.thermal_zones_from_internal_zones:
                self._check_extra_thermal_zone(thermal_zone)

  def test_enrichment(self):
    """
    Test enrichment of the city with different orders
    :return: None
    """
    file_1 = 'one_building_in_kelowna.gml'
    self._test_hft(file_1)
    file_2 = 'C40_Final.gml'
    self._test_hft(file_2)
